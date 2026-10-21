"""JSON file persistence with one lock around each read-modify-write cycle."""

import json
import os
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path


def empty_state():
    return {"next_id": 1, "items": [], "dishes": []}


def allocate_id(state):
    """Hand out the next id. Items and dishes share one counter."""
    new_id = state["next_id"]
    state["next_id"] += 1
    return new_id


class JsonStore:
    """Keeps the shopping list and the dishes in one JSON document."""

    def __init__(self, path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def exists(self):
        return self.path.exists()

    def load(self):
        """Return the stored state, or an empty one if the file is missing."""
        # Reads take the lock too: on Windows, os.replace fails while another thread has the file open.
        with self._lock:
            return self._read()

    @contextmanager
    def update(self):
        """Yield the state for changes and save it if the block finishes without an error."""
        with self._lock:
            state = self._read()
            yield state
            self._save(state)

    def _read(self):
        if not self.path.exists():
            return empty_state()
        with self.path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def _save(self, state):
        # Write to a temp file and swap it in, so a reader never sees half a document.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".shoplist-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(state, fh, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
