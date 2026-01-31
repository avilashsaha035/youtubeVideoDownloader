# 🎬 Tube Downloader

A simple YouTube video downloader built with **Python**.  
It provides a clean web interface where users can paste a YouTube link, preview the video thumbnail and title, choose the desired quality (1080p, 720p, 480p, or best available), and download the video directly to their machine.

---

## ✨ Features
- Paste a YouTube link and instantly see the **thumbnail** and **title**.
- Choose from multiple **video qualities** before downloading.
- Downloads are named with the **actual video title**.
- Lightweight server — no heavy frameworks used.
- Clean and responsive frontend with a loader spinner while fetching video info.

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/tube-downloader.git
cd tube-downloader
```

### 2. Install dependencies
```bash
# yt-dlp
python -m pip install -U "yt-dlp[default]"
```
- download **ffmpeg** from https://www.gyan.dev/ffmpeg/builds/

### 3. Start the server
```bash
python server.py
```
### 4. The server will start at:
```bash
http://127.0.0.1:8000
```
