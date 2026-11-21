import hmac
import html
import json
import os
import re
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


HOST = "0.0.0.0"
PORT = int(os.environ.get("IMAGE_RECEIVER_PORT", "8000"))
MAX_IMAGE_SIZE = 10 * 1024 * 1024
UPLOAD_TOKEN = os.environ.get("PI_UPLOAD_TOKEN")
IMAGE_DIRECTORY = Path(__file__).resolve().parent / "motion_captures"
IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)


class ImageReceiverHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            self._show_gallery()
            return
        if path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if path.startswith("/images/"):
            self._show_image(path[len("/images/"):])
            return
        self.send_error(404, "Not found")

    def do_POST(self):
        if urlsplit(self.path).path != "/upload":
            self.send_error(404, "Not found")
            return

        if UPLOAD_TOKEN:
            provided_token = self.headers.get("X-Upload-Token", "")
            if not hmac.compare_digest(provided_token, UPLOAD_TOKEN):
                self._send_json(401, {"error": "Invalid upload token"})
                return

        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.send_error(411, "Content-Length is required")
            return

        if content_length <= 0:
            self._send_json(400, {"error": "The image is empty"})
            return
        if content_length > MAX_IMAGE_SIZE:
            self._send_json(413, {"error": "Image exceeds the 10 MB limit"})
            return

        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        image_format = {
            "image/jpeg": ("jpg", b"\xff\xd8\xff"),
            "image/png": ("png", b"\x89PNG\r\n\x1a\n"),
        }.get(content_type)
        if image_format is None:
            self._send_json(415, {"error": "Only JPEG and PNG images are accepted"})
            return

        image_data = self.rfile.read(content_length)
        if len(image_data) != content_length:
            self._send_json(400, {"error": "Incomplete image upload"})
            return

        extension, signature = image_format
        if not image_data.startswith(signature):
            self._send_json(400, {"error": "Image data does not match its content type"})
            return

        filename = "{}_{}.{}".format(
            datetime.now().strftime("%Y%m%d_%H%M%S"),
            uuid.uuid4().hex[:8],
            extension,
        )
        destination = IMAGE_DIRECTORY / filename
        with destination.open("xb") as image_file:
            image_file.write(image_data)

        self._send_json(201, {"saved": filename})
        print("Received image: {}".format(destination), flush=True)

    def _show_gallery(self):
        images = sorted(
            (
                path for path in IMAGE_DIRECTORY.iterdir()
                if path.is_file() and path.suffix.lower() in (".jpg", ".jpeg", ".png")
            ),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        cards = "".join(
            '<figure><a href="/images/{0}"><img src="/images/{0}" alt="{0}"></a>'
            "<figcaption>{0}</figcaption></figure>".format(html.escape(path.name, quote=True))
            for path in images
        )
        if not cards:
            cards = "<p>No images received yet.</p>"
        page = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>Pi Camera Gallery</title>"
            "<style>body{{font:16px sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem}}"
            ".gallery{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem}}"
            "figure{{margin:0}}img{{width:100%;height:200px;object-fit:cover;background:#eee}}"
            "figcaption{{overflow-wrap:anywhere;padding:.4rem 0}}</style></head><body>"
            "<h1>Pi Camera Gallery</h1><p>Received images: {} &middot; "
            "<a href='/'>Refresh</a></p>"
            "<div class='gallery'>{}</div></body></html>"
        ).format(len(images), cards).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def _show_image(self, requested_name):
        filename = unquote(requested_name)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", filename):
            self.send_error(404, "Image not found")
            return
        image_path = IMAGE_DIRECTORY / filename
        if not image_path.is_file() or image_path.parent != IMAGE_DIRECTORY:
            self.send_error(404, "Image not found")
            return
        content_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
        image_data = image_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(image_data)))
        self.end_headers()
        self.wfile.write(image_data)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), ImageReceiverHandler)
    print("Image receiver listening on port {}.".format(PORT))
    print("Open http://<this-computer-ip>:{}/ in a browser.".format(PORT))
    if UPLOAD_TOKEN:
        print("Uploads require the X-Upload-Token header.")
    else:
        print("No upload token is set; only run this on a trusted network.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping image receiver.")
    finally:
        server.server_close()