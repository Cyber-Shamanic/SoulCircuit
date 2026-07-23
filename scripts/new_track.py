#!/usr/bin/env python3
"""Create a SoulCircuit track folder from the canonical template."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates/track"
TRACKS = ROOT / "albums/01-soul-circuit/tracks"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("track_id", help="Track ID such as SC-03")
    parser.add_argument("slug", help="Lowercase kebab-case slug")
    parser.add_argument("title_he", help="Hebrew display title")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the destination without writing files",
    )
    return parser.parse_args()


def validate(track_id: str, slug: str) -> None:
    if not re.fullmatch(r"SC-\d{2}", track_id):
        raise ValueError("track_id must match SC-XX")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("slug must be lowercase kebab-case")


def render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def main() -> int:
    args = parse_args()
    try:
        validate(args.track_id, args.slug)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    destination = TRACKS / f"{args.track_id}-{args.slug}"
    if destination.exists():
        print(f"ERROR: destination already exists: {destination}", file=sys.stderr)
        return 3

    values = {
        "TRACK_ID": args.track_id,
        "SLUG": args.slug,
        "TITLE_HE": args.title_he,
        "DATE": date.today().isoformat(),
    }

    if args.dry_run:
        print(f"Dry run passed: {destination}")
        return 0

    destination.mkdir(parents=True)
    for source in sorted(TEMPLATE.iterdir()):
        if not source.is_file():
            continue
        output = destination / source.name
        output.write_text(render(source.read_text(encoding="utf-8"), values), encoding="utf-8")

    print(f"Created: {destination}")
    print("Next: add the track to catalog/tracks.yml and the album sequence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
