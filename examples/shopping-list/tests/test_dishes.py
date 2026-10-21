import pytest

from shoplist.dishes import DishBook
from shoplist.model import NotFound, ValidationError
from shoplist.samples import add_samples

PASTA = [
    {"name": "Spaghetti", "amount": 500, "unit": "g", "category": "Vorrat"},
    {"name": "Salz"},
]


@pytest.fixture
def book(store):
    return DishBook(store)


def test_create_and_get_a_dish(book):
    dish = book.create(" Pasta  Pomodoro ", 2, PASTA)
    assert dish["name"] == "Pasta Pomodoro"
    assert dish["ingredients"] == [
        {"name": "Spaghetti", "amount": 500.0, "unit": "g", "category": "Vorrat"},
        {"name": "Salz", "amount": None, "unit": "", "category": "Sonstiges"},
    ]
    assert book.get(dish["id"]) == dish


@pytest.mark.parametrize(
    "name, servings, ingredients, message",
    [
        ("", 2, PASTA, "Gericht darf nicht leer sein"),
        ("Pasta", 0, PASTA, "Portionen"),
        ("Pasta", 2.5, PASTA, "Portionen"),
        ("Pasta", 51, PASTA, "Portionen"),
        ("Pasta", 2, [], "mindestens eine Zutat"),
        ("Pasta", 2, None, "mindestens eine Zutat"),
        ("Pasta", 2, ["Salz"], "Jede Zutat"),
        ("Pasta", 2, [{"name": " "}], "Zutat darf nicht leer sein"),
    ],
)
def test_create_rejects_invalid_dishes(book, store, name, servings, ingredients, message):
    with pytest.raises(ValidationError, match=message):
        book.create(name, servings, ingredients)
    assert not store.exists()


def test_dishes_are_sorted_by_name(book):
    add_samples(book)
    assert [dish["name"] for dish in book.dishes()] == ["Gemüsecurry", "Pfannkuchen", "Spaghetti Bolognese"]


def test_delete_a_dish(book):
    dish = book.create("Pasta", 2, PASTA)
    book.delete(dish["id"])
    assert book.dishes() == []
    with pytest.raises(NotFound, match=f"Gericht {dish['id']} gibt es nicht"):
        book.get(dish["id"])
    with pytest.raises(NotFound):
        book.delete(dish["id"])
