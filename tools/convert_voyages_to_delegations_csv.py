import argparse
from pathlib import Path

from delegations_csv import export_delegations_csv
from parser_trips import load_voyages


def parse_args():
    parser = argparse.ArgumentParser(
        description="Konwertuje legacy Voyage.xml do publicznego delegations.csv"
    )
    parser.add_argument("voyages_xml", help="Ścieżka do legacy Voyage.xml")
    parser.add_argument("out_csv", help="Ścieżka wyjściowa delegations.csv")
    return parser.parse_args()


def main():
    args = parse_args()
    trips = load_voyages(Path(args.voyages_xml))
    export_delegations_csv(trips, args.out_csv)
    print(f"Zapisano {len(trips)} delegacji do {args.out_csv}")


if __name__ == "__main__":
    main()
