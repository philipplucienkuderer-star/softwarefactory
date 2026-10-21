"""HTTP layer: serves the mobile page and a JSON API.

The `Api` handlers are the orchestration layer. They turn requests into
service calls, and service results or errors into responses.
"""

import json
import re
import traceback
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .dishes import DishBook
from .model import CATEGORIES, NotFound, ValidationError
from .shopping import ShoppingList

STATIC_DIR = Path(__file__).parent / "static"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json"),
    "/icon.svg": ("icon.svg", "image/svg+xml"),
}
MAX_BODY_BYTES = 64 * 1024


@dataclass(frozen=True)
class Request:
    ids: tuple
    query: dict
    body: dict


class Api:
    """Maps API routes to service calls. Every handler returns (status, payload)."""

    def __init__(self, shopping, dishes):
        self.shopping = shopping
        self.dishes = dishes
        self.routes = [
            ("GET", r"/api/categories", self.list_categories),
            ("GET", r"/api/items", self.list_items),
            ("POST", r"/api/items", self.add_item),
            ("DELETE", r"/api/items/checked", self.remove_checked),
            ("PATCH", r"/api/items/(\d+)", self.check_item),
            ("GET", r"/api/dishes", self.list_dishes),
            ("POST", r"/api/dishes", self.create_dish),
            ("GET", r"/api/dishes/(\d+)", self.get_dish),
            ("DELETE", r"/api/dishes/(\d+)", self.delete_dish),
        ]

    def dispatch(self, method, path, query, body):
        path_known = False
        for route_method, pattern, handler in self.routes:
            match = re.fullmatch(pattern, path)
            if not match:
                continue
            path_known = True
            if route_method != method:
                continue
            try:
                return handler(Request(tuple(int(group) for group in match.groups()), query, body))
            except ValidationError as exc:
                return HTTPStatus.BAD_REQUEST, {"error": str(exc)}
            except NotFound as exc:
                return HTTPStatus.NOT_FOUND, {"error": str(exc)}
        if path_known:
            return HTTPStatus.METHOD_NOT_ALLOWED, {"error": "Methode nicht erlaubt."}
        return HTTPStatus.NOT_FOUND, {"error": "Nicht gefunden."}

    def list_categories(self, request):
        return HTTPStatus.OK, {"categories": list(CATEGORIES)}

    def list_items(self, request):
        return HTTPStatus.OK, {"items": self.shopping.items()}

    def add_item(self, request):
        body = request.body
        item = self.shopping.add_item(
            body.get("name"), body.get("amount"), body.get("unit"), body.get("category")
        )
        return HTTPStatus.CREATED, {"item": item}

    def check_item(self, request):
        checked = request.body.get("checked")
        if not isinstance(checked, bool):
            raise ValidationError("Feld 'checked' muss true oder false sein.")
        return HTTPStatus.OK, {"item": self.shopping.set_checked(request.ids[0], checked)}

    def remove_checked(self, request):
        return HTTPStatus.OK, {"removed": self.shopping.remove_checked()}

    def list_dishes(self, request):
        return HTTPStatus.OK, {"dishes": self.dishes.dishes()}

    def create_dish(self, request):
        body = request.body
        dish = self.dishes.create(body.get("name"), body.get("servings"), body.get("ingredients"))
        return HTTPStatus.CREATED, {"dish": dish}

    def get_dish(self, request):
        return HTTPStatus.OK, {"dish": self.dishes.get(request.ids[0])}

    def delete_dish(self, request):
        self.dishes.delete(request.ids[0])
        return HTTPStatus.OK, {"deleted": request.ids[0]}


def build_api(store):
    return Api(ShoppingList(store), DishBook(store))


def make_handler(api):
    class Handler(BaseHTTPRequestHandler):
        server_version = "shoplist"

        def do_GET(self):
            url = urlsplit(self.path)
            if url.path in STATIC_FILES:
                name, content_type = STATIC_FILES[url.path]
                self._send(HTTPStatus.OK, (STATIC_DIR / name).read_bytes(), content_type)
            else:
                self._handle_api()

        def do_POST(self):
            self._handle_api()

        do_PATCH = do_DELETE = do_POST

        def _handle_api(self):
            url = urlsplit(self.path)
            try:
                body = self._read_body()
            except ValidationError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            try:
                status, payload = api.dispatch(self.command, url.path, parse_qs(url.query), body)
            except Exception:
                self.log_error("%s", traceback.format_exc())
                status, payload = HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Interner Fehler."}
            self._send_json(status, payload)

        def _read_body(self):
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                raise ValidationError("Ungültige Content-Length.") from None
            if length < 0 or length > MAX_BODY_BYTES:
                raise ValidationError("Anfrage ist zu groß.")
            if not length:
                return {}
            try:
                body = json.loads(self.rfile.read(length))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ValidationError("Anfrage ist kein gültiges JSON.") from None
            if not isinstance(body, dict):
                raise ValidationError("Erwartet wird ein JSON-Objekt.")
            return body

        def _send_json(self, status, payload):
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send(status, data, "application/json; charset=utf-8", cache="no-store")

        def _send(self, status, data, content_type, cache="no-cache"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", cache)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

    return Handler


def make_server(api, host="127.0.0.1", port=8765):
    return ThreadingHTTPServer((host, port), make_handler(api))


def serve(api, host, port, out):
    server = make_server(api, host, port)
    print(f"Shopping list running at http://{host}:{server.server_port}/ (Ctrl+C stops)", file=out, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
