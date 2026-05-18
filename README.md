

```markdown
# 🎨 IconArchive Perfect Selective Downloader

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Active-brightgreen.svg" alt="Status">
</p>
```
An advanced, multi-threaded, and highly customizable Python scraper designed to download massive icon sets from [IconArchive.com](https://www.iconarchive.com) flawlessly.

This tool goes beyond simple downloading. It features smart skipping, missing-file detection, selective format filtering, **advanced tag scraping**, and a powerful **static JSON API generator** to make your local icon collection instantly searchable and web-ready.

---

## ✨ Core Features

- **🚀 Multi-Threaded Performance:** Uses Python's `ThreadPoolExecutor` for lightning-fast, concurrent downloading of hundreds of icons simultaneously.
- **🧠 Smart Resuming & Updating:** Built-in logic checks for existing files. If a download was interrupted, or if new icons were added to the site, it will **only download the missing files**—saving massive amounts of bandwidth and time.
- **🎯 Selective Format Filtering:** Choose exactly what you want to download. Target specific formats like `vector`, `png`, `mac`, `windows`, `favicon`, or download them `all`.
- **📂 Automated Batch Processing:** Provide a list of your favorite designers in a simple `Designer.txt` file to download and organize dozens of artist pages automatically.
- **🏷️ Advanced Tag Scraping:** Automatically extracts and saves all relevant tags for each icon into a `tags.json` manifest, making your collection easy to search.
- **⚡ Static JSON API Generation:** After downloading, the script automatically builds a lightweight, queryable JSON API of your entire collection. It creates a `master_index.json` and a structured `data/` directory, perfect for powering web galleries, search tools, or other applications.
- **🛡️ Safe & Resilient:** Gracefully handles network errors, connection timeouts, and HTTP `429 Too Many Requests` rate-limits by implementing intelligent retries and back-off delays.
- **🗂️ Perfectly Organized Output:** Automatically organizes everything into a clean `Designer / Artist / Set / Format` folder structure, complete with JSON manifests for easy tracking.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.7+

### Steps

**1. Clone the repository:**
It's recommended to use a virtual environment to keep dependencies isolated.
```bash
# Clone the project
git clone https://github.com/yourusername/IconArchive-Downloader.git
cd IconArchive-Downloader

# (Optional but Recommended) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

**2. Install required Python packages:**
```bash
pip install requests beautifulsoup4 lxml tqdm
```

**3. Create your `Designer.txt` list:**
Create a text file named `Designer.txt` in the root directory of the project. Add the names of the artists (exactly as they appear in the IconArchive URL), with one artist name per line.

*Example (`Designer.txt`):*
```text
papirus-team
justicon
gartoon-team
```
*(If you run the script without this file, it will automatically create this template for you).*

---

## 💻 Usage & CLI Commands

The script features a flexible command-line interface. You can mix and match **Artists**, **Action Flags**, and **Formats** to create precise commands.

### 📝 Available Arguments
- **Action Flags:**
    - `update`: Checks existing artist folders and downloads only missing files.
    - `force`: A powerful alias for `update`.
- **Formats:** `vector`, `png`, `mac`, `windows`, `favicon`
- **Artists:** Any unrecognized word is treated as a specific artist name to target.

---

### 🌟 Examples

**1. Default Batch Run (Smart Skip)**
Reads `Designer.txt`. If an artist folder already exists, it **skips** them completely. It downloads all formats for any new artists found in the list.
```bash
python iconarchive_perfect_selective.py
```

**2. Update Everything (Fill in the Blanks)**
Reads `Designer.txt` and forces a scan on *all artists*, including already downloaded ones. It checks the website, compares it to your local files, and downloads **only what is missing**. This is perfect for keeping your collection up-to-date.
```bash
python iconarchive_perfect_selective.py update
```

**3. Download Specific Formats Only (e.g., Vector & PNG)**
Reads `Designer.txt` but will *only* download Vector and PNG files for all artists.
```bash
python iconarchive_perfect_selective.py vector png
```

**4. Force Update a Specific Format**
Checks all artists in `Designer.txt` and downloads any missing Vector files, even if the artist folder already exists. Your existing PNGs and other formats will remain untouched.
```bash
python iconarchive_perfect_selective.py update vector
```

**5. Target a Specific Artist**
Ignores `Designer.txt` and only processes `papirus-team`. Downloads all available formats for them.
```bash
python iconarchive_perfect_selective.py papirus-team
```

**6. The Ultimate Precision Command**
Scans *only* the `papirus-team` artist. It forces an `update` check on their folders and downloads **only missing Vector and PNG files**.
```bash
python iconarchive_perfect_selective.py papirus-team update vector png
```

---

## 📁 Output Folder Structure

The script generates two main output directories: `Designer/` for the raw icon files and `data/` for the structured JSON API.

### Icon Asset Structure (`Designer/`)

```text
.
├── 📄 iconarchive_perfect_selective.py
├── 📄 Designer.txt
└── 📂 Designer/
    └── 📂 Papirus-Team/              <-- Artist Name (formatted)
        └── 📂 Papirus-Apps/         <-- Set Name
            │
            ├── 📂 Vector/          <-- Format Category
            │   ├── 0ad.svg
            │   └── amazon.svg
            │
            ├── 📂 PNG/             <-- Format Category
            │   ├── 0ad.png
            │   └── amazon.png
            │
            ├── 📄 Vector.json      <-- Manifest of downloaded Vector files
            ├── 📄 PNG.json         <-- Manifest of downloaded PNG files
            └── 📄 tags.json         <-- **Valuable icon tags for this set**
```

### Static API Structure (`data/` and `master_index.json`)

This structure is automatically re-generated at the end of each run, providing a clean, ready-to-use API.

```text
.
├── 📄 master_index.json            <-- High-level overview of all artists & counts
└── 📂 data/
    ├── 📂 designers/
    │   └── papirus-team.json      <-- Lists all icon sets for this designer
    │
    └── 📂 packs/
        └── 📂 papirus-team/
            ├── papirus-apps.json  <-- Detailed list of all icons in this pack
            └── papirus-places.json
```

---

## ⚙️ How It Works

1.  **Parse Arguments:** The script first reads your CLI commands to determine the mode (default, update), target formats, and specific artists.
2.  **Identify Artists:** It either reads the `Designer.txt` file or uses the artists specified in the command.
3.  **Scrape Icon Sets:** For each artist, it visits their main page and scrapes the URLs for all of their icon sets.
4.  **Intelligent Pagination:** Instead of clicking "next," the script calculates all page URLs for a set mathematically for maximum efficiency.
5.  **Concurrent Icon Discovery:** It fetches all pages of an icon set concurrently to gather a master list of all individual icon URLs.
6.  **Concurrent Downloading:** It processes each icon URL in a thread pool. For each icon:
    - It scrapes the available download links and associated tags.
    - It checks if a file for a desired format already exists.
    - If the file is missing, it downloads it and saves it to the correct `Artist/Set/Format` directory.
    - It updates the corresponding JSON manifests (`Vector.json`, `tags.json`, etc.).
7.  **Build Static API:** Once all downloads are complete, it scans the entire `Designer/` directory to build the `master_index.json` and the structured `data/` folder API.

---

## ⚠️ Disclaimer

This tool is intended for educational purposes and for creating personal archives of publicly available data. Please be respectful of IconArchive's servers. The default multi-threading settings are designed to be efficient but not aggressive. Do not abuse the script to overwhelm the website.

You are responsible for ensuring you adhere to the licensing terms of the individual artists whose work you are downloading. Each artist and icon set on IconArchive has its own usage license—please respect them.

---

**Developed with ❤️ for Icon Enthusiasts & Data Hoarders.**
```
