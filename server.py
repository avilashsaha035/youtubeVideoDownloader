import http.server
import socketserver
import urllib.parse
import yt_dlp
import os
import tempfile

PORT = 8000

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "index.html"
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == "/download":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode("utf-8"))
            url = params.get("url", [""])[0]

            if url:
                try:
                    # Create a temporary file path
                    tmpdir = tempfile.gettempdir()
                    outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")

                    ydl_opts = {
                        "format": "bestvideo+bestaudio/best",
                        "merge_output_format": "mp4",
                        "outtmpl": outtmpl,
                    }

                    # Download to temp file
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        filename = ydl.prepare_filename(info)

                    filesize = os.path.getsize(filename)

                    # Get actual title of the yt video
                    video_title = info.get("title", "video")
                    basename = f"{video_title}.mp4"

                    # Send headers with Content-Length
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Disposition", f"attachment; filename=\"{basename}\"")
                    self.send_header("Content-Length", str(filesize))
                    self.end_headers()

                    # Stream file to browser
                    with open(filename, "rb") as f:
                        for chunk in iter(lambda: f.read(8192), b""):
                            self.wfile.write(chunk)

                    # Remove temp file after streaming
                    os.remove(filename)

                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Download failed: {e}".encode("utf-8"))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid URL")

Handler = MyHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at http://127.0.0.1:{PORT}")
    httpd.serve_forever()
