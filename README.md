# 🎨 IconArchive Perfect Selective Downloader

An advanced, multi-threaded, and highly customizable Python scraper designed to download massive icon sets from [IconArchive.com](https://www.iconarchive.com) flawlessly. 

It features smart skipping, missing-file detection, selective format filtering (Vector, PNG, Mac, Windows, Favicon), and a robust Command Line Interface (CLI).

---

## ✨ Features

- **🚀 Multi-Threaded:** Uses Python's `ThreadPoolExecutor` for lightning-fast, concurrent downloading.
- **🧠 Smart Resuming & Updating:** Built-in logic checks existing files. If a download was interrupted, or if new icons were added to the site, it will **only download the missing files**—saving massive amounts of bandwidth and time.
- **🎯 Selective Formats:** Choose exactly what you want: `vector`, `png`, `mac`, `windows`, `favicon`, or `all`.
- **📂 Batch Processing:** Read a list of designers/artists from a simple `Designer.txt` file to process dozens of pages automatically.
- **🛡️ Safe & Resilient:** Handles HTTP `429 Too Many Requests` rate-limits, connection timeouts, and missing elements gracefully.
- **🗂️ Clean Output:** Automatically organizes everything perfectly into `Artist / Set / Format` folders, complete with JSON manifests.

---

## 🛠️ Installation & Setup

**1. Clone the repository:**
```bash
git clone https://github.com/yourusername/IconArchive-Downloader.git
cd IconArchive-Downloader
```



**2. Install required Python packages:**
```bash
pip install requests beautifulsoup4 lxml tqdm
```

**3. Create your `Designer.txt` list:**
Create a text file named `Designer.txt` in the same directory as the script. Add the names of the artists (exactly as they appear in the IconArchive URL), one per line. 
*Example (`Designer.txt`):*
```text
papirus-team
justicon
gartoon-team
```
*(If you run the script without this file, it will automatically create a template for you).*

---

## 💻 Usage & CLI Commands

The script features a very flexible command-line interface. You can mix and match **Artists**, **Action Flags**, and **Formats**.

### 📝 Available Arguments
- **Action Flags:** `update`, `force`, `all`
- **Formats:** `vector`, `png`, `mac`, `windows`, `favicon`
- **Artists:** Any unrecognized word is treated as a specific artist name.

---

### 🌟 Examples

**1. Default Batch Run (Smart Skip)**
Reads `Designer.txt`. If an artist folder already exists, it **skips** them completely to save time. Downloads all formats for new artists.
```bash
python iconarchive_perfect_selective.py
```

**2. Update Everything (Fill in the blanks)**
Reads `Designer.txt`, but forces a scan on *already downloaded* artists. It checks the website and compares it to your local files, downloading **only what is missing**.
```bash
python iconarchive_perfect_selective.py update
```

**3. Download Specific Formats Only (e.g., Vector & PNG)**
Reads `Designer.txt` but will *only* download Vector and PNG files.
```bash
python iconarchive_perfect_selective.py vector png
```

**4. Force Update a Specific Format for Everything**
Checks all artists in `Designer.txt` and downloads any missing Vector files, even if the artist folder already exists. (Keeps your existing PNGs untouched!)
```bash
python iconarchive_perfect_selective.py force vector
```

**5. Target a Specific Artist**
Ignores `Designer.txt` and only processes `papirus-team`. Downloads all formats.
```bash
python iconarchive_perfect_selective.py papirus-team
```

**6. Target a Specific Artist + Update + Specific Formats**
Scans *only* `papirus-team`. It checks their folders and downloads **only missing Vector and PNG files**.
```bash
python iconarchive_perfect_selective.py papirus-team update vector png
```

---

## 📁 Output Folder Structure

The script will automatically create a root folder called `iconarchive` and organize files like this:

```text
📂 (Your Current Working Directory)
 │
 ├── 📄 iconarchive_perfect_selective.py    <-- The main Python script
 ├── 📄 Designer.txt                        <-- List of artists to download
 ├── 📄 master_index.json                   <-- Re-built automatically at the end!
 │
 └── 📂 iconarchive/
      │
      └── 📂 Designer/
           │
           ├── 📂 Papirus-Team/             <-- Artist Name
           │    │
           │    ├── 📂 Papirus-Apps/        <-- Set Name
           │    │    │
           │    │    ├── 📂 Vector/         <-- Format Category
           │    │    │    ├── 0ad.svg
           │    │    │    ├── amazon.svg
           │    │    │    └── ... (all vector icons)
           │    │    │
           │    │    ├── 📂 PNG/            <-- Format Category
           │    │    │    ├── 0ad.png
           │    │    │    ├── amazon.png
           │    │    │    └── ... (all png icons)
           │    │    │
           │    │    ├── 📄 Vector.json     <-- Tracks downloaded Vector files
           │    │    └── 📄 PNG.json        <-- Tracks downloaded PNG files
           │    │
           │    └── 📂 Papirus-Places/      <-- Another Set
           │         ├── 📂 Vector/
           │         │    └── ...
           │         └── 📄 Vector.json
           │
           └── 📂 Justicon/                 <-- Another Artist
                │
                └── 📂 Medical-Icons/
                     ├── 📂 PNG/
                     │    └── ...
                     └── 📄 PNG.json
    ...
```

---

## ⚠️ Disclaimer

This tool is for educational purposes and personal archival. Please be respectful to IconArchive's servers. Do not abuse the multi-threading logic to execute Denial of Service attacks. Ensure you follow the licensing terms of the individual artists whose work you are downloading. 

---

**Developed with ❤️ for Icon Enthusiasts & Data Hoarders.**
```
