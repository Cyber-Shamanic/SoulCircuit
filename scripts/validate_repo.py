#!/usr/bin/env python3
"""Validate SoulCircuit's repository structure without third-party packages."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "README.md",
    "ALBUM.md",
    "TRACKLIST.md",
    "ROADMAP.md",
    "catalog/tracks.yml",
    "catalog/themes.yml",
    "templates/track/README.md",
    "templates/track/lyrics.md",
    "templates/track/production.md",
    "templates/track/artwork.md",
    "templates/track/sources.yml",
    "templates/track/review.md",
    "albums/01-soul-circuit/sequence.yml",
]

TRACK_FILES = {
    "README.md",
    "lyrics.md",
    "production.md",
    "artwork.md",
    "sources.yml",
    "review.md",
}

ALLOWED_STATUSES = {
    "seed",
    "sources",
    "draft",
    "lyrics-lock",
    "production",
    "mix",
    "master",
    "released",
}


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def validate_required(errors: list[str]) -> None:
    for relative in REQUIRED_PATHS:
        if not (ROOT / relative).exists():
            fail(f"Missing required path: {relative}", errors)


def validate_catalog(errors: list[str]) -> set[str]:
    text = read("catalog/tracks.yml")
    ids = re.findall(r"^\s+- id:\s*(SC-\d{2})\s*$", text, re.MULTILINE)
    if len(ids) != len(set(ids)):
        fail("Duplicate track IDs in catalog/tracks.yml", errors)

    orders = [int(value) for value in re.findall(r"^\s+order:\s*(\d+)\s*$", text, re.MULTILINE)]
    if sorted(orders) != list(range(1, len(orders) + 1)):
        fail("Album order values must be unique and contiguous from 1", errors)

    statuses = re.findall(r"^\s+status:\s*([a-z-]+)\s*$", text, re.MULTILINE)
    invalid_statuses = sorted(set(statuses) - ALLOWED_STATUSES)
    if invalid_statuses:
        fail(f"Invalid statuses: {', '.join(invalid_statuses)}", errors)

    return set(ids)


def validate_sequence(catalog_ids: set[str], errors: list[str]) -> None:
    text = read("albums/01-soul-circuit/sequence.yml")
    sequence = re.findall(r"^\s+-\s+(SC-\d{2})\s*$", text, re.MULTILINE)
    if len(sequence) != 12:
        fail(f"Album 01 sequence must contain 12 tracks; found {len(sequence)}", errors)
    if len(sequence) != len(set(sequence)):
        fail("Album 01 sequence contains duplicate IDs", errors)
    missing = sorted(set(sequence) - catalog_ids)
    if missing:
        fail(f"Sequence IDs missing from catalog: {', '.join(missing)}", errors)


def validate_master_map(catalog_ids: set[str], errors: list[str]) -> None:
    text = read("TRACKLIST.md")
    listed_ids = set(re.findall(r"\|\s*(SC-\d{2})\s*\|", text))
    expected_ids = {f"SC-{number:02d}" for number in range(1, 41)}
    if listed_ids != expected_ids:
        missing = sorted(expected_ids - listed_ids)
        extra = sorted(listed_ids - expected_ids)
        if missing:
            fail(f"TRACKLIST.md missing master IDs: {', '.join(missing)}", errors)
        if extra:
            fail(f"TRACKLIST.md has unexpected IDs: {', '.join(extra)}", errors)
    if catalog_ids != expected_ids:
        missing = sorted(expected_ids - catalog_ids)
        extra = sorted(catalog_ids - expected_ids)
        if missing:
            fail(f"Catalog missing master IDs: {', '.join(missing)}", errors)
        if extra:
            fail(f"Catalog has unexpected IDs: {', '.join(extra)}", errors)


def validate_track_folders(errors: list[str]) -> None:
    tracks_root = ROOT / "albums/01-soul-circuit/tracks"
    for folder in sorted(tracks_root.glob("SC-[0-9][0-9]-*")):
        missing = TRACK_FILES - {item.name for item in folder.iterdir() if item.is_file()}
        if missing:
            fail(f"{folder.relative_to(ROOT)} missing: {', '.join(sorted(missing))}", errors)


def validate_templates(errors: list[str]) -> None:
    placeholders = {"{{TRACK_ID}}", "{{TITLE_HE}}"}
    for relative in (
        "templates/track/README.md",
        "templates/track/lyrics.md",
        "templates/track/production.md",
        "templates/track/artwork.md",
    ):
        text = read(relative)
        absent = placeholders - set(re.findall(r"\{\{[A-Z_]+\}\}", text))
        if absent:
            fail(f"{relative} missing placeholders: {', '.join(sorted(absent))}", errors)


def validate_local_markdown_links(errors: list[str]) -> None:
    pattern = re.compile(r"\]\(([^)]+)\)")
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in pattern.findall(text):
            target = target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith(("mailto:", "#", "+")):
                continue
            candidate = (path.parent / target).resolve()
            try:
                candidate.relative_to(ROOT.resolve())
            except ValueError:
                fail(f"{path.relative_to(ROOT)} links outside repository: {target}", errors)
                continue
            if not candidate.exists():
                fail(f"{path.relative_to(ROOT)} has broken link: {target}", errors)


def main() -> int:
    errors: list[str] = []
    validate_required(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    catalog_ids = validate_catalog(errors)
    validate_sequence(catalog_ids, errors)
    validate_master_map(catalog_ids, errors)
    validate_track_folders(errors)
    validate_templates(errors)
    validate_local_markdown_links(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"\nValidation failed with {len(errors)} error(s).")
        return 1

    print("SoulCircuit validation passed.")
    print(f"Catalog tracks: {len(catalog_ids)}")
    print("Album 01 sequence: 12")
    print("Quality gates: 12")
    return 0


if __name__ == "__main__":
    sys.exit(main())
