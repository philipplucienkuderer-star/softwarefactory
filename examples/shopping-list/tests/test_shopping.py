import pytest

from shoplist.model import NotFound, ValidationError
from shoplist.shopping import ShoppingList


@pytest.fixture
def shopping(store):
    return ShoppingList(store)


def test_add_item_cleans_input_and_saves_it(shopping, store):
    item = shopping.add_item("  Frische   Milch ", 1, " l ", "Kühlregal")
    assert item == {
        "id": 1,
        "name": "Frische Milch",
        "amount": 1.0,
        "unit": "l",
        "category": "Kühlregal",
        "checked": False,
    }
    assert store.load()["items"] == [item]


def test_add_item_without_amount_or_category(shopping):
    item = shopping.add_item("Spülmittel")
    assert (item["amount"], item["unit"], item["category"]) == (None, "", "Sonstiges")


@pytest.mark.parametrize(
    "fields, message",
    [
        ({"name": "  "}, "Artikel darf nicht leer sein"),
        ({"name": "x" * 81}, "höchstens 80 Zeichen"),
        ({"name": "Milch", "amount": 0}, "größer als 0"),
        ({"name": "Milch", "amount": float("nan")}, "größer als 0"),
        ({"name": "Milch", "amount": "viel"}, "Menge muss eine Zahl sein"),
        ({"name": "Milch", "amount": True}, "Menge muss eine Zahl sein"),
        ({"name": "Milch", "unit": "x" * 13}, "Einheit darf höchstens"),
        ({"name": "Milch", "category": "Spielzeug"}, "Unbekannte Kategorie"),
    ],
)
def test_add_item_rejects_invalid_input(shopping, store, fields, message):
    with pytest.raises(ValidationError, match=message):
        shopping.add_item(**fields)
    assert not store.exists()


def test_items_follow_the_walk_through_the_store(shopping):
    shopping.add_item("Shampoo", category="Drogerie")
    shopping.add_item("Äpfel", category="Obst & Gemüse")
    shopping.add_item("Brot", category="Backwaren")
    shopping.add_item("Bananen", category="Obst & Gemüse")
    assert [item["name"] for item in shopping.items()] == ["Äpfel", "Bananen", "Brot", "Shampoo"]


def test_checked_items_can_be_cleared(shopping):
    milk = shopping.add_item("Milch")
    shopping.add_item("Brot")
    assert shopping.set_checked(milk["id"], True)["checked"] is True
    assert shopping.remove_checked() == 1
    assert [item["name"] for item in shopping.items()] == ["Brot"]


def test_checking_an_unknown_item_fails(shopping):
    with pytest.raises(NotFound, match="Artikel 99 gibt es nicht"):
        shopping.set_checked(99, True)
