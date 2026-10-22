import threading

import pytest

from shoplist.shopping import ShoppingList


def test_load_without_file_returns_empty_state(store):
    assert store.load() == {"next_id": 1, "items": [], "dishes": []}
    assert not store.exists()


def test_update_saves_changes(store):
    with store.update() as state:
        state["next_id"] = 5
    assert store.load()["next_id"] == 5


def test_update_discards_changes_after_an_error(store):
    with store.update() as state:
        state["next_id"] = 5
    with pytest.raises(RuntimeError):
        with store.update() as state:
            state["next_id"] = 99
            raise RuntimeError("boom")
    assert store.load()["next_id"] == 5
    assert [path.name for path in store.path.parent.iterdir()] == ["shoplist.json"]


def test_parallel_updates_keep_every_write(store):
    shopping = ShoppingList(store)
    threads = [threading.Thread(target=shopping.add_item, args=(f"Artikel {n}",)) for n in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    ids = [item["id"] for item in shopping.items()]
    assert sorted(ids) == list(range(1, 21))
