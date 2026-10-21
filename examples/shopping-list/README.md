# Shopping list (example project)

A small mobile web app for planning groceries, built to try out the agent
skills in this repo. The interface is German; the code and docs are English.

The app has two tabs:

- `Liste` holds what you need to buy. Each item has an amount, a unit and a
  category, and you tick items off as they go into the cart. Items are grouped
  by category in the order of a walk through a typical German supermarket.
- `Gerichte` holds dishes with servings and ingredients. Open one to see what
  it needs, and use − and + to change the servings. The amounts follow.
  `Zutaten auf die Liste` puts every ingredient on the shopping list. If two
  dishes need the same thing in the same unit, the list shows it once with
  the amounts added up and names the dishes it is for. A fresh install starts
  with three sample dishes.

It needs Python 3.10+ and nothing outside the standard library. The page ships
a web app manifest, so a phone can add it to the home screen.

## Run it

```bash
cd examples/shopping-list
python -m shoplist                 # http://127.0.0.1:8765/
python -m shoplist --host 0.0.0.0  # reach it from a phone on the same Wi-Fi
```

Data lives in `shoplist.json` in the current directory. Pass `--data` to use
another file and `--no-samples` to start without the sample dishes. There is
no login, so only use `--host 0.0.0.0` on a network you trust.

## Test it

```bash
cd examples/shopping-list
python -m pip install pytest
python -m pytest -q
```

## Layout

| Path | Role |
|---|---|
| `shoplist/store.py` | JSON file storage. One lock covers each read-modify-write cycle. Every save writes a temp file and swaps it in. |
| `shoplist/model.py` | Input rules, categories and errors that both services share. |
| `shoplist/shopping.py` | `ShoppingList` service: add and merge, tick off, clear. |
| `shoplist/dishes.py` | `DishBook` service: create, list, show, scale, delete dishes. |
| `shoplist/web.py` | HTTP layer. `Api` turns requests into service calls and holds no business rules. |
| `shoplist/static/` | The mobile page: plain HTML, CSS and JavaScript with no build step. |

The services own validation, ordering, merging and ids. The web layer only
turns requests into service calls. Putting a dish on the list, for example,
asks `DishBook` for the scaled dish and hands its ingredients to
`ShoppingList.add_items`. Typing an item by hand goes through the same merge,
so both paths follow one rule. A CLI or another front end could reuse the
services as they are.
