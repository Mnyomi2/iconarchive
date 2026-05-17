import os
import sys
import re
import json
import time
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

BASE = "https://www.iconarchive.com"
ROOT_DIR = "Designer"
DESIGNER_DIR = "Designer"
API_DIR = "api_data" # New folder for decentralized JSON API

# --- THREAD-SAFE BROWSER SESSIONS ---
thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        s = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3, pool_connections=8, pool_maxsize=8)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"})
        thread_local.session = s
    return thread_local.session

# ---------- Safe Network Functions ----------
def get_soup(url):
    s = get_session()
    for _ in range(5):
        try:
            time.sleep(0.05)
            r = s.get(url, timeout=(10, 15))
            if r.status_code == 404: return None
            if r.status_code == 429: 
                time.sleep(5)
                continue
            r.raise_for_status()
            return BeautifulSoup(r.text, "lxml")
        except Exception:
            time.sleep(2)
    return None

def download_file(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return True 
        
    s = get_session()
    for _ in range(5):
        try:
            with s.get(url, stream=True, timeout=(10, 20)) as r:
                if r.status_code == 404: return False
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
            return True
        except Exception:
            time.sleep(2)
    return False

# ---------- Step 1: Find Sets ----------
def get_sets(artist_url):
    s = get_soup(artist_url)
    if not s: return []
    
    sets = []
    for div in s.select("div.iconset"):
        preview_a = div.select_one("div.s-preview a")
        if not preview_a: continue
            
        href = preview_a.get("href")
        img = preview_a.find("img")
        
        title = img.get("alt") if img and img.get("alt") else ""
        if not title:
            h2 = div.select_one("h2")
            title = h2.text if h2 else "Unknown-Set"
            
        folder_name = title.strip().replace(" ", "-")
        folder_name = re.sub(r"[^\w\-]", "", folder_name)
        
        if href:
            sets.append((folder_name, urljoin(BASE, href)))
            
    return sets

# ---------- Step 2: MATHEMATICAL PAGINATION ----------
def get_all_pages(start_url):
    s = get_soup(start_url)
    if not s: return [start_url]
    
    max_page = 1
    page_links = s.select("div.paginationnumbers a")
    for a in page_links:
        try:
            num = int(a.text.strip())
            if num > max_page: max_page = num
        except ValueError: pass
            
    pages = []
    base_str = start_url.replace('.html', '')
    if base_str.endswith('.1'): base_str = base_str[:-2]
        
    for i in range(1, max_page + 1):
        if i == 1: pages.append(f"{base_str}.html")
        else: pages.append(f"{base_str}.{i}.html")
            
    if not pages: pages = [start_url]
    return pages

# ---------- Step 3: Analyze Icon Formats ----------
def get_icon_downloads(icon_url):
    data = {"Vector": [], "PNG": [], "Favicon": [], "Windows": [], "Mac": []}
    s = get_soup(icon_url)
    if not s: return data
    
    table = s.select_one("table.down")
    if table:
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 2: continue
            
            cat_text = tds[0].text.strip().lower()
            links = [urljoin(BASE, a['href']) for a in tds[1].find_all("a", href=True) if '/download/' in a['href']]
            
            for lnk in links:
                if "vector" in cat_text: data["Vector"].append(lnk)
                elif "png" in cat_text: data["PNG"].append(lnk)
                elif "favicon" in cat_text: data["Favicon"].append(lnk)
                elif "windows" in cat_text: data["Windows"].append(lnk)
                elif "mac" in cat_text: data["Mac"].append(lnk)
    return data

# ---------- Step 4: JSON Manager ----------
manifest_lock = threading.Lock()
def update_json(folder, category, filename):
    json_path = os.path.join(folder, f"{category}.json")
    with manifest_lock:
        data = []
        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as f: data = json.load(f)
            except Exception: pass
        if filename not in data:
            data.append(filename)
            data = sorted(list(set(data)))
            with open(json_path, "w") as f: json.dump(data, f, indent=2)

# ---------- Step 5: Core Processor ----------
def process_set(artist_dir, set_name, set_url, selected_categories):
    print(f"\n{'='*50}\n📁 Processing: {set_name}\n{'='*50}")
    folder = os.path.join(artist_dir, set_name)
    os.makedirs(folder, exist_ok=True)
    
    pages = get_all_pages(set_url)
    
    icon_urls = []
    def fetch_page_icons(p):
        s = get_soup(p)
        if s: return [urljoin(BASE, a["href"]) for a in s.select("div.icondetail a") if a.get("href")]
        return []

    with ThreadPoolExecutor(max_workers=8) as exe:
        futures = [exe.submit(fetch_page_icons, p) for p in pages]
        for f in tqdm(as_completed(futures), total=len(pages), desc="Indexing Pages", unit="page"):
            icon_urls.extend(f.result())
            
    icon_urls = list(set(icon_urls))

    def process_single_icon(icon_url):
        downloads = get_icon_downloads(icon_url)
        for category, links in downloads.items():
            if category not in selected_categories or not links: continue
            cat_folder = os.path.join(folder, category)
            os.makedirs(cat_folder, exist_ok=True)
            for dlink in links:
                filename = dlink.split('/')[-1]
                filepath = os.path.join(cat_folder, filename)
                if download_file(dlink, filepath):
                    update_json(folder, category, filename)

    if icon_urls:
        with ThreadPoolExecutor(max_workers=6) as exe:
            list(tqdm(exe.map(process_single_icon, icon_urls), total=len(icon_urls), desc="Downloading", unit="icon"))

# ---------- Step 6: MODULAR API INDEX BUILDER ----------
def build_index():
    print(f"\n{'='*60}\n🔍 Building Modular API Database...\n{'='*60}")
    
    valid_extensions = {'.svg', '.png', '.ico', '.icns'}
    base_dir = "." 
    os.makedirs(API_DIR, exist_ok=True)
    
    # 1. Map entire directory into memory
    tree = {}
    for root, dirs, files in os.walk(DESIGNER_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in valid_extensions: continue
                
            rel_path = os.path.relpath(os.path.join(root, file), base_dir).replace('\\', '/')
            parts = rel_path.split('/')
            
            if len(parts) >= 4:
                artist = parts[-4].replace('-', ' ')
                pack = parts[-3].replace('-', ' ')
                fmt = parts[-2]
                
                if artist not in tree: tree[artist] = {}
                if pack not in tree[artist]: tree[artist][pack] = []
                
                tree[artist][pack].append({
                    "format": fmt,
                    "name": file,
                    "path": rel_path
                })

    # 2. Build lightweight master index & split JSONs
    master_index = {}
    
    def get_priority(f):
        f = f.lower()
        if 'vector' in f: return 1
        if 'png' in f: return 2
        return 3

    for artist, packs in tree.items():
        artist_safe = artist.replace(' ', '_')
        os.makedirs(os.path.join(API_DIR, artist_safe), exist_ok=True)
        
        master_index[artist] = {"total_icons": 0, "packs": {}}
        
        for pack, icons in packs.items():
            pack_safe = pack.replace(' ', '_')
            
            # Save API file (Minified for speed)
            api_file_path = os.path.join(API_DIR, artist_safe, f"{pack_safe}.json")
            with open(api_file_path, 'w', encoding='utf-8') as f:
                json.dump(icons, f, separators=(',', ':'))

            # Process Meta Data for Master Index
            unique_bases = set(i['name'].split('.')[0].lower() for i in icons)
            unique_count = len(unique_bases)
            master_index[artist]["total_icons"] += unique_count
            
            sorted_icons = sorted(icons, key=lambda x: get_priority(x['format']))
            
            previews = []
            seen_base = set()
            for ic in sorted_icons:
                b = ic['name'].split('.')[0].lower()
                if b not in seen_base:
                    seen_base.add(b)
                    previews.append(ic)
                if len(previews) == 4: break
                    
            master_index[artist]["packs"][pack] = {
                "icon_count": unique_count,
                "previews": previews
            }

    # Write Master Index (Now extremely tiny and fast!)
    with open('master_index.json', 'w', encoding='utf-8') as f:
        json.dump(master_index, f, indent=2)
        
    print(f"✅ Success! Generated master index and API endpoints in '{API_DIR}/'")

# ---------- Entry Point ----------
def main():
    os.makedirs(DESIGNER_DIR, exist_ok=True)
    args = [a.lower() for a in sys.argv[1:]]
    category_map = {"vector": "Vector", "png": "PNG", "favicon": "Favicon", "windows": "Windows", "mac": "Mac"}
    
    selected_categories = [category_map[a] for a in args if a in category_map] or list(category_map.values())
    force_update = "update" in args or "force" in args
    reserved = ["all", "update", "force"] + list(category_map.keys())
    specific_artists = [a for a in sys.argv[1:] if a.lower() not in reserved]

    artists = specific_artists
    if not artists:
        if not os.path.exists("Designer.txt"):
            with open("Designer.txt", "w") as f: f.write("papirus-team\njusticon\ngartoon-team\n")
            print("📝 Template 'Designer.txt' created! Run script again.")
            return
        with open("Designer.txt", "r", encoding="utf-8") as f:
            artists = [line.strip() for line in f if line.strip()]

    for name in artists:
        artist_dir = os.path.join(DESIGNER_DIR, "-".join(w.capitalize() for w in name.split("-")))
        if os.path.exists(artist_dir) and not force_update and any(os.scandir(artist_dir)):
            print(f"⏩ Skipping '{name}'. Use 'update' to rescan.")
            continue
            
        sets = get_sets(f"https://www.iconarchive.com/artist/{name}.html")
        for s_name, s_url in sets: process_set(artist_dir, s_name, s_url, selected_categories)

    build_index()

if __name__ == "__main__":
    main()
