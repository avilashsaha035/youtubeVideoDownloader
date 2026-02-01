import http.server
import socketserver
import urllib.parse
import yt_dlp
import os
import tempfile
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

PORT = int(os.environ.get("PORT", 8000))

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "index.html"
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == "/probe":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode("utf-8"))
            url = params.get("url", [""])[0]

            if not url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Missing URL"}).encode("utf-8"))
                return

            try:
                probe_opts = {
                    "format": "bestvideo+bestaudio/best",
                    "skip_download": True,
                    "quiet": True,
                }
                with yt_dlp.YoutubeDL(probe_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                title = info.get("title", "")
                thumbnail = info.get("thumbnail", "")

                qualities_set = set()
                formats = info.get("formats", []) or []
                for f in formats:
                    if f.get("vcodec") != "none" and f.get("height"):
                        qualities_set.add(int(f.get("height")))

                qualities = sorted(list(qualities_set), reverse=True)
                quality_items = [{"label": f"{h}p", "value": f"{h}p"} for h in qualities]

                resp = {"success": True, "title": title, "thumbnail": thumbnail, "qualities": quality_items}
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))

            except Exception as e:
                logging.error("Probe failed", exc_info=True)
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        if self.path == "/download":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode("utf-8"))
            url = params.get("url", [""])[0]
            quality = params.get("quality", ["best"])[0]

            if url:
                try:
                    tmpdir = tempfile.gettempdir()
                    outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")

                    quality_map = {
                        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                        "best": "bestvideo+bestaudio/best"
                    }

                    fmt = quality_map.get(quality)
                    if not fmt and quality.endswith("p"):
                        try:
                            h = int(quality[:-1])
                            fmt = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"
                        except Exception:
                            fmt = "bestvideo+bestaudio/best"
                    if not fmt:
                        fmt = "bestvideo+bestaudio/best"

                    ydl_opts = {
                        "format": fmt,
                        "merge_output_format": "mp4",
                        "outtmpl": outtmpl,
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        filename = ydl.prepare_filename(info)

                    filesize = os.path.getsize(filename)
                    video_title = info.get("title", "video")
                    safe_title = "".join(c for c in video_title if c.isalnum() or c in " .-_()[]").strip()
                    basename = f"{safe_title}.mp4"

                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Disposition", f"attachment; filename=\"{basename}\"")
                    self.send_header("Content-Length", str(filesize))
                    self.end_headers()

                    with open(filename, "rb") as f:
                        for chunk in iter(lambda: f.read(8192), b""):
                            self.wfile.write(chunk)

                    os.remove(filename)

                except Exception as e:
                    logging.error("Download failed", exc_info=True)
                    self.send_response(500)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Download failed: {e}".encode("utf-8"))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid URL")
            return

        return http.server.SimpleHTTPRequestHandler.do_POST(self)


if __name__ == "__main__":
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), MyHandler) as httpd:
        logging.info(f"Serving at http://0.0.0.0:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("Server stopped manually")
