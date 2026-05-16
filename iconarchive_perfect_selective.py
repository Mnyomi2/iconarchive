
cat > iconarchive_perfect_selective.py << 'EOF'

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
            if num > max_page:
                max_page = num
        except ValueError:
            pass
            
    pages = []
    base_str = start_url.replace('.html', '')
    if base_str.endswith('.1'): 
        base_str = base_str[:-2]
        
    for i in range(1, max_page + 1):
        if i == 1:
            pages.append(f"{base_str}.html")
        else:
            pages.append(f"{base_str}.{i}.html")
            
    if not pages:
        pages = [start_url]
        
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
                with open(json_path, "r") as f:
                    data = json.load(f)
            except Exception:
                pass
        
        if filename not in data:
            data.append(filename)
            data = sorted(list(set(data)))
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)

# ---------- Step 5: Core Processor ----------
def process_set(artist_dir, set_name, set_url, selected_categories):
    print(f"\n{'='*50}\n📁 Processing: {set_name}\n{'='*50}")
    folder = os.path.join(artist_dir, set_name)
    os.makedirs(folder, exist_ok=True)
    
    pages = get_all_pages(set_url)
    print(f"📄 Generated {len(pages)} calculated pages.")
    
    icon_urls = []
    def fetch_page_icons(p):
        s = get_soup(p)
        if s:
            return [urljoin(BASE, a["href"]) for a in s.select("div.icondetail a") if a.get("href")]
        return []

    with ThreadPoolExecutor(max_workers=8) as exe:
        futures = [exe.submit(fetch_page_icons, p) for p in pages]
        for f in tqdm(as_completed(futures), total=len(pages), desc="Indexing Pages", unit="page"):
            icon_urls.extend(f.result())
            
    icon_urls = list(set(icon_urls))
    print(f"🖼️ Found {len(icon_urls)} total icons. Starting extraction...")

    def process_single_icon(icon_url):
        downloads = get_icon_downloads(icon_url)
        
        for category, links in downloads.items():
            if category not in selected_categories:
                continue
                
            if not links: continue
            
            cat_folder = os.path.join(folder, category)
            os.makedirs(cat_folder, exist_ok=True)
            
            for dlink in links:
                filename = dlink.split('/')[-1]
                filepath = os.path.join(cat_folder, filename)
                
                success = download_file(dlink, filepath)
                if success:
                    update_json(folder, category, filename)

    if icon_urls:
        with ThreadPoolExecutor(max_workers=6) as exe:
            list(tqdm(exe.map(process_single_icon, icon_urls), total=len(icon_urls), desc="Downloading", unit="icon"))

# ---------- Step 6: Index Builder ----------
def build_index():
    print(f"\n{'='*60}\n🔍 Scanning folders to build master index...\n{'='*60}")
    data = []
    
    valid_extensions = {'.svg', '.png', '.ico', '.icns'}
    base_dir = "." 
    
    if not os.path.exists(base_dir):
        print(f"⚠️ Directory {base_dir} does not exist yet. Skipping index build.")
        return

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.startswith('.') or file.endswith('.json') or file.endswith('.html') or file.endswith('.py'):
                continue
                
            ext = os.path.splitext(file)[1].lower()
            if ext not in valid_extensions:
                continue
                
            # Path will now look like: Designer/Papirus-Team/Papirus-Apps/Vector/0ad.svg
            rel_path = os.path.relpath(os.path.join(root, file), base_dir)
            parts = rel_path.replace('\\', '/').split('/')
            
            # Count backwards safely finds Artist, Set, Format regardless of nested root folders
            if len(parts) >= 4:
                artist = parts[-4]
                icon_set = parts[-3]
                format_type = parts[-2]
                
                data.append({
                    "artist": artist.replace('-', ' '),
                    "set": icon_set.replace('-', ' '),
                    "format": format_type,
                    "name": file,
                    "path": "/".join(parts) # Web safe path
                })

    data = sorted(data, key=lambda x: (x['artist'], x['set'], x['name']))

    output_file = 'master_index.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    print(f"✅ Success! Found {len(data)} icons.")
    print(f"📁 Saved to {output_file}")


# ---------- Entry Point ----------
def main():
    # Make sure ROOT_DIR and DESIGNER_DIR both exist
    os.makedirs(DESIGNER_DIR, exist_ok=True)
    
    args = sys.argv[1:]
    args_lower = [a.lower() for a in args]

    category_map = {
        "vector": "Vector",
        "png": "PNG",
        "favicon": "Favicon",
        "windows": "Windows",
        "mac": "Mac"
    }
    
    selected_categories = [category_map[a] for a in args_lower if a in category_map]
    
    if not selected_categories:
        selected_categories = list(category_map.values())

    force_update = "update" in args_lower or "force" in args_lower

    reserved_words = ["all", "update", "force"] + list(category_map.keys())
    specific_artists = [a for a in args if a.lower() not in reserved_words]

    artists_to_process = []
    
    if specific_artists:
        artists_to_process = specific_artists
    else:
        if not os.path.exists("Designer.txt"):
            print("❌ Designer.txt not found! Creating a template for you...")
            with open("Designer.txt", "w") as f:
                f.write("papirus-team\njusticon\ngartoon-team\n")
            print("📝 Template 'Designer.txt' created! Run the script again.")
            return
            
        with open("Designer.txt", "r", encoding="utf-8") as f:
            artists_to_process = [line.strip() for line in f if line.strip()]
            
    if not artists_to_process:
        print("❌ No artists found to process.")
        return

    print(f"✅ Categories to download: {', '.join(selected_categories)}")
    print(f"✅ Update/Force Mode: {'ON' if force_update else 'OFF'}")

    for artist_name in artists_to_process:
        artist_url = f"https://www.iconarchive.com/artist/{artist_name}.html"
        
        artist_dir_name = "-".join(word.capitalize() for word in artist_name.split("-"))
        # Save inside iconarchive/Designer/
        artist_dir = os.path.join(DESIGNER_DIR, artist_dir_name)
        
        print(f"\n{'='*60}\n👨‍🎨 Processing Artist: {artist_name}\n{'='*60}")
        
        if os.path.exists(artist_dir) and not force_update:
            if any(os.scandir(artist_dir)):
                print(f"⏩ Skipping '{artist_dir_name}' (Already exists).")
                print("   Use 'update' or 'force' argument to scan for missing files.")
                continue

        os.makedirs(artist_dir, exist_ok=True)
        print(f"📁 Base Directory: {artist_dir}")
        print("🔍 Fetching Set Information...")
        
        sets = get_sets(artist_url)
        
        if not sets:
            print(f"❌ Could not find any sets for {artist_name}. Please check the URL/Name.")
            continue
            
        print(f"✅ Found {len(sets)} Sets.")
        
        for set_name, set_url in sets:
            process_set(artist_dir, set_name, set_url, selected_categories)

    build_index()
    print("\n🎉 ALL FINISHED PERFECTLY!")

if __name__ == "__main__":
    main()
