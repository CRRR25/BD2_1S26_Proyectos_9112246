"""
Punto de entrada del contenedor data-generator.

Uso (dentro del contenedor):
    python main.py --all              # genera CSV + esquema + carga + stats
    python main.py --generate         # solo genera CSV
    python main.py --schema           # solo aplica esquema (constraints/indexes)
    python main.py --load             # solo ejecuta LOAD CSV
    python main.py --reset            # vacia la base de datos
    python main.py --stats            # muestra conteos
"""

import argparse

import generator
import loader


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all",      action="store_true")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--schema",   action="store_true")
    parser.add_argument("--load",     action="store_true")
    parser.add_argument("--reset",    action="store_true")
    parser.add_argument("--stats",    action="store_true")
    args = parser.parse_args()

    did_something = False

    if args.reset:
        loader.reset_db()
        did_something = True

    if args.all or args.generate:
        generator.generate_all("/app/data")
        did_something = True

    if args.all or args.schema:
        loader.load_schema()
        did_something = True

    if args.all or args.load:
        loader.load_data()
        did_something = True

    if args.all or args.stats:
        loader.stats()
        did_something = True

    if not did_something:
        parser.print_help()


if __name__ == "__main__":
    main()
