import pytest

from conftest import OPENER


@pytest.mark.parametrize(
    "path, content_type",
    [
        ("/", "text/html"),
        ("/app.js", "text/javascript"),
        ("/style.css", "text/css"),
        ("/manifest.webmanifest", "application/manifest+json"),
        ("/icon.svg", "image/svg+xml"),
    ],
)
def test_page_and_assets_are_served(server, path, content_type):
    with OPENER.open(server + path) as response:
        assert response.status == 200
        assert response.headers["Content-Type"].startswith(content_type)


def test_categories_come_in_store_walk_order(client):
    status, body = client("GET", "/api/categories")
    assert status == 200
    assert body["categories"][0] == "Obst & Gemüse"
    assert body["categories"][-1] == "Sonstiges"


def test_add_check_and_clear_an_item(client):
    status, body = client("POST", "/api/items", {"name": "Milch", "amount": 1.5, "unit": "l", "category": "Kühlregal"})
    assert status == 201
    item_id = body["item"]["id"]

    status, body = client("PATCH", f"/api/items/{item_id}", {"checked": True})
    assert (status, body["item"]["checked"]) == (200, True)
    assert client("GET", "/api/items")[1]["items"][0]["checked"] is True

    assert client("DELETE", "/api/items/checked") == (200, {"removed": 1})
    assert client("GET", "/api/items") == (200, {"items": []})


def test_create_show_and_delete_a_dish(client):
    status, body = client(
        "POST",
        "/api/dishes",
        {"name": "Pfannkuchen", "servings": 2, "ingredients": [{"name": "Mehl", "amount": 250, "unit": "g"}]},
    )
    assert status == 201
    dish_id = body["dish"]["id"]

    assert client("GET", f"/api/dishes/{dish_id}")[1]["dish"]["ingredients"][0]["name"] == "Mehl"
    assert [dish["name"] for dish in client("GET", "/api/dishes")[1]["dishes"]] == ["Pfannkuchen"]
    assert client("DELETE", f"/api/dishes/{dish_id}") == (200, {"deleted": dish_id})
    assert client("GET", f"/api/dishes/{dish_id}") == (404, {"error": f"Gericht {dish_id} gibt es nicht."})


def test_a_dish_can_be_scaled_and_put_on_the_list(client):
    _, body = client(
        "POST",
        "/api/dishes",
        {
            "name": "Pfannkuchen",
            "servings": 2,
            "ingredients": [
                {"name": "Mehl", "amount": 250, "unit": "g", "category": "Vorrat"},
                {"name": "Eier", "amount": 3, "unit": "Stk", "category": "Kühlregal"},
            ],
        },
    )
    dish_id = body["dish"]["id"]

    status, body = client("GET", f"/api/dishes/{dish_id}?servings=4")
    assert status == 200
    assert [ingredient["amount"] for ingredient in body["dish"]["ingredients"]] == [500.0, 6.0]

    assert client("POST", f"/api/dishes/{dish_id}/shop", {"servings": 4}) == (200, {"added": 2})
    assert client("POST", f"/api/dishes/{dish_id}/shop", {"servings": 2}) == (200, {"added": 2})
    items = client("GET", "/api/items")[1]["items"]
    assert [(item["name"], item["amount"], item["sources"]) for item in items] == [
        ("Eier", 9.0, ["Pfannkuchen"]),
        ("Mehl", 750.0, ["Pfannkuchen"]),
    ]


@pytest.mark.parametrize(
    "method, path, body, raw, status, error",
    [
        ("POST", "/api/items", {"name": ""}, None, 400, "Artikel darf nicht leer sein."),
        ("POST", "/api/items", None, b"{nope", 400, "Anfrage ist kein gültiges JSON."),
        ("POST", "/api/items", None, b"[1, 2]", 400, "Erwartet wird ein JSON-Objekt."),
        ("PATCH", "/api/items/1", {"checked": "ja"}, None, 400, "Feld 'checked' muss true oder false sein."),
        ("PATCH", "/api/items/7", {"checked": True}, None, 404, "Artikel 7 gibt es nicht."),
        ("POST", "/api/dishes", {"name": "Leer", "servings": 2, "ingredients": []}, None, 400,
         "Ein Gericht braucht mindestens eine Zutat."),
        ("GET", "/api/dishes/1?servings=zwei", None, None, 400, "Portionen müssen eine ganze Zahl von 1 bis 50 sein."),
        ("POST", "/api/dishes/9/shop", {"servings": 2}, None, 404, "Gericht 9 gibt es nicht."),
        ("DELETE", "/api/items", None, None, 405, "Methode nicht erlaubt."),
        ("GET", "/api/nichts", None, None, 404, "Nicht gefunden."),
    ],
)
def test_api_errors_are_json(client, method, path, body, raw, status, error):
    assert client(method, path, body, raw) == (status, {"error": error})
