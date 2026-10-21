# Shopping list (example project)

A small mobile web app for planning groceries, built to try out the agent
skills in this repo. The interface is German; the code and docs are English.

The app has two tabs:

- `Liste` holds what you need to buy. Each item has an amount, a unit and a
  category, and you tick items off as they go into the cart. Items are grouped
  by category in the order of a walk through a typical German supermarket.
- `Gerichte` holds dishes with servings and ingredients. Open one to see what
  it needs. A fresh install starts with three sample dishes.

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
| `shoplist/shopping.py` | `ShoppingList` service: add, tick off, clear. |
| `shoplist/dishes.py` | `DishBook` service: create, list, show, delete dishes. |
| `shoplist/web.py` | HTTP layer. `Api` turns requests into service calls and holds no business rules. |
| `shoplist/static/` | The mobile page: plain HTML, CSS and JavaScript with no build step. |

The services own validation, ordering and ids. The web layer only turns
requests into service calls, so a CLI or another front end could reuse the
services as they are.
