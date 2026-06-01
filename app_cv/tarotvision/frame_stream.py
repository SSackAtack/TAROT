"""Tiny MJPEG preview server for the browser Studio console."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time

import cv2


class LatestFrameStore:
    def __init__(self, jpeg_quality=75, max_width=960):
        self.jpeg_quality = jpeg_quality
        self.max_width = max_width
        self._lock = threading.Lock()
        self._jpeg = None

    def update(self, frame):
        if frame is None:
            return
        preview = frame
        height, width = preview.shape[:2]
        if width > self.max_width:
            scale = self.max_width / float(width)
            preview = cv2.resize(preview, (self.max_width, int(height * scale)))
        ok, encoded = cv2.imencode(
            ".jpg",
            preview,
            [int(cv2.IMWRITE_JPEG_QUALITY), int(self.jpeg_quality)],
        )
        if not ok:
            return
        with self._lock:
            self._jpeg = encoded.tobytes()

    def get(self):
        with self._lock:
            return self._jpeg


def make_preview_handler(frame_store):
    class PreviewHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def do_GET(self):
            if self.path.startswith("/health"):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"ok")
                return

            if not self.path.startswith("/video_feed.mjpg"):
                self.send_response(404)
                self.end_headers()
                return

            self.send_response(200)
            self.send_header("Age", "0")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()

            while True:
                jpeg = frame_store.get()
                if jpeg is None:
                    time.sleep(0.05)
                    continue
                try:
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(jpeg)}\r\n\r\n".encode("ascii"))
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                    time.sleep(0.1)
                except (BrokenPipeError, ConnectionResetError):
                    break

    return PreviewHandler


def start_preview_server(frame_store, host="localhost", port=8766):
    server = ThreadingHTTPServer((host, port), make_preview_handler(frame_store))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
