import json
import threading
import urllib.error
import urllib.request

import pytest

from shoplist.store import JsonStore
from shoplist.web import build_api, make_server

# Talk to the local test server directly, even if the machine has a proxy configured.
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


@pytest.fixture
def store(tmp_path):
    return JsonStore(tmp_path / "shoplist.json")


@pytest.fixture
def server(store):
    httpd = make_server(build_api(store), port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture
def client(server):
    """Send one API request and return (status, decoded JSON body)."""

    def call(method, path, body=None, raw=None):
        data = raw if raw is not None else None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            server + path, data=data, method=method, headers={"Content-Type": "application/json"}
        )
        try:
            with OPENER.open(request) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    return call
