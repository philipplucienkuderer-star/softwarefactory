"""Shopping list operations."""

from .model import CATEGORIES, clean_entry, find_by_id
from .store import allocate_id


def _matches(item, entry):
    """An open item with the same name and unit absorbs a new entry."""
    return (
        not item["checked"]
        and item["name"].casefold() == entry["name"].casefold()
        and item["unit"].casefold() == entry["unit"].casefold()
    )


def _merge(state, entry, source):
    item = next((item for item in state["items"] if _matches(item, entry)), None)
    if item is None:
        item = {"id": allocate_id(state), **entry, "checked": False, "sources": []}
        state["items"].append(item)
    elif entry["amount"] is not None:
        item["amount"] = round((item["amount"] or 0) + entry["amount"], 2)
    sources = item.setdefault("sources", [])
    if source and source not in sources:
        sources.append(source)
    return item


class ShoppingList:
    """Adds, checks off and clears items on the shopping list."""

    def __init__(self, store):
        self.store = store

    def items(self):
        """Return all items in store-walk order: by category, then in the order they were added."""
        return sorted(self.store.load()["items"], key=lambda item: CATEGORIES.index(item["category"]))

    def add_item(self, name, amount=None, unit="", category=None):
        """Put one item on the list and return it, merged with an open item of the same name and unit."""
        return self.add_items([{"name": name, "amount": amount, "unit": unit, "category": category}])[0]

    def add_items(self, entries, source=None):
        """Put several items on the list in one save and return the resulting items.

        `source` names the dish the entries come from. Every entry is checked
        before anything is saved, so one bad entry leaves the list unchanged.
        """
        cleaned = [clean_entry(entry, "Artikel") for entry in entries]
        with self.store.update() as state:
            items = [_merge(state, entry, source) for entry in cleaned]
        return items

    def set_checked(self, item_id, checked):
        """Tick an item off or put it back. Raises NotFound for unknown ids."""
        with self.store.update() as state:
            item = find_by_id(state["items"], item_id, "Artikel")
            item["checked"] = bool(checked)
        return item

    def remove_checked(self):
        """Delete every ticked item and return how many were removed."""
        with self.store.update() as state:
            kept = [item for item in state["items"] if not item["checked"]]
            removed = len(state["items"]) - len(kept)
            state["items"] = kept
        return removed
