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
