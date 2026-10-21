"""Command-line entry point: python -m shoplist [--data FILE] [--host HOST] [--port PORT]."""

import argparse
import sys

from .dishes import DishBook
from .samples import add_samples
from .store import JsonStore
from .web import build_api, serve


def build_parser():
    parser = argparse.ArgumentParser(prog="shoplist", description="Serve the mobile shopping list.")
    parser.add_argument(
        "--data", default="shoplist.json", help="JSON file with the list and the dishes (default: %(default)s)"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="use 0.0.0.0 to open the page from a phone on the same network"
    )
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-samples", action="store_true", help="start without the three example dishes")
    return parser


def main(argv=None, out=None):
    args = build_parser().parse_args(argv)
    store = JsonStore(args.data)
    if not store.exists() and not args.no_samples:
        add_samples(DishBook(store))
    serve(build_api(store), args.host, args.port, out or sys.stdout)
    return 0
