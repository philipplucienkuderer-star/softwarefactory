"""Shopping list operations."""

from .model import CATEGORIES, clean_amount, clean_category, clean_name, clean_unit, find_by_id
from .store import allocate_id


class ShoppingList:
    """Adds, checks off and clears items on the shopping list."""

    def __init__(self, store):
        self.store = store

    def items(self):
        """Return all items in store-walk order: by category, then in the order they were added."""
        return sorted(self.store.load()["items"], key=lambda item: CATEGORIES.index(item["category"]))

    def add_item(self, name, amount=None, unit="", category=None):
        item = {
            "name": clean_name(name, "Artikel"),
            "amount": clean_amount(amount),
            "unit": clean_unit(unit),
            "category": clean_category(category),
            "checked": False,
        }
        with self.store.update() as state:
            item = {"id": allocate_id(state), **item}
            state["items"].append(item)
        return item

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
