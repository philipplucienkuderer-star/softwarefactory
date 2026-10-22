"""Dishes and the ingredients they need."""

from .model import ValidationError, clean_entry, clean_name, find_by_id
from .store import allocate_id

MAX_SERVINGS = 50
MAX_INGREDIENTS = 40


def clean_servings(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_SERVINGS:
        raise ValidationError(f"Portionen müssen eine ganze Zahl von 1 bis {MAX_SERVINGS} sein.")
    return value


def clean_ingredient(raw):
    if not isinstance(raw, dict):
        raise ValidationError("Jede Zutat braucht Name, Menge, Einheit und Kategorie.")
    return clean_entry(raw, "Zutat")


class DishBook:
    """Creates, lists, scales and deletes dishes."""

    def __init__(self, store):
        self.store = store

    def dishes(self):
        return sorted(self.store.load()["dishes"], key=lambda dish: dish["name"].casefold())

    def get(self, dish_id):
        """Return one dish. Raises NotFound for unknown ids."""
        return find_by_id(self.store.load()["dishes"], dish_id, "Gericht")

    def scaled(self, dish_id, servings):
        """Return the dish with every amount converted to `servings`. The stored dish stays as it is."""
        servings = clean_servings(servings)
        dish = self.get(dish_id)
        factor = servings / dish["servings"]
        ingredients = [
            {**ingredient, "amount": None if ingredient["amount"] is None else round(ingredient["amount"] * factor, 2)}
            for ingredient in dish["ingredients"]
        ]
        return {**dish, "servings": servings, "ingredients": ingredients}

    def create(self, name, servings, ingredients):
        if not isinstance(ingredients, list) or not ingredients:
            raise ValidationError("Ein Gericht braucht mindestens eine Zutat.")
        if len(ingredients) > MAX_INGREDIENTS:
            raise ValidationError(f"Ein Gericht kann höchstens {MAX_INGREDIENTS} Zutaten haben.")
        dish = {
            "name": clean_name(name, "Gericht"),
            "servings": clean_servings(servings),
            "ingredients": [clean_ingredient(raw) for raw in ingredients],
        }
        with self.store.update() as state:
            dish = {"id": allocate_id(state), **dish}
            state["dishes"].append(dish)
        return dish

    def delete(self, dish_id):
        with self.store.update() as state:
            dish = find_by_id(state["dishes"], dish_id, "Gericht")
            state["dishes"].remove(dish)
