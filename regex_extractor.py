"""Extract common data formats from text or validate a single field value."""

import argparse
import json
from pathlib import Path
import re
import sys


# Dotted ASCII domain with no hyphen at either end of a label.
DOMAIN = r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}"
EMAIL_ATOM = r"[A-Za-z0-9_+%'-]+"
URL_CHAR = r"(?:[A-Za-z0-9._~:/?#@!$&*+,;=\-]|%[0-9A-Fa-f]{2})"
TAG_NAME = r"[A-Za-z][A-Za-z0-9:-]*"
ATTRIBUTE = r"""[^\s"'<>/=]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'`=<>]+))?"""

PATTERNS = {
    "emails": re.compile(
        rf"(?<![\w.+%'@-]){EMAIL_ATOM}(?:\.{EMAIL_ATOM})*@{DOMAIN}"
        r"(?![\w@-]|\.+\w)"
    ),
    "urls": re.compile(
        rf"(?<![\w+./-])(?ai:https?)://{DOMAIN}(?::[0-9]{{1,5}})?"
        rf"(?:[/?#]{URL_CHAR}*)?"
        r"""(?![\w/%#?@-]|\.+\w|:[^\s)>\]"',;!?])"""
    ),
    "phones": re.compile(
        r"(?<![\w+])(?<![0-9][ .-])"
        r"(?:\([0-9]{3}\)[ \t]*[0-9]{3}-[0-9]{4}"
        r"|[0-9]{3}(?P<phone_sep>[ .-])[0-9]{3}(?P=phone_sep)[0-9]{4})"
        r"(?!\w|[ .-][0-9])"
    ),
    "credit_cards": re.compile(
        r"(?<![\w-])(?<![0-9][ -])[0-9]{4}(?P<card_sep>[ -])"
        r"(?:[0-9]{4}(?P=card_sep)){2}[0-9]{4}(?![\w-]| [0-9])"
    ),
    "times": re.compile(
        r"(?<![\w:])(?:"
        r"(?:0?[1-9]|1[0-2]):[0-5][0-9][ \t]+[AP]M"
        r"|(?:[01][0-9]|2[0-3]):[0-5][0-9](?![ \t]+[AP]M\b)"
        r")(?![\w:])",
        re.IGNORECASE,
    ),
    "html_tags": re.compile(
        rf"<(?:/{TAG_NAME}\s*|{TAG_NAME}(?:\s+{ATTRIBUTE})*\s*/?)>"
    ),
    "hashtags": re.compile(r"(?<![\w#/=&])#\w+"),
    "currencies": re.compile(
        r"(?<![\w$+-])\$(?:[1-9][0-9]{0,2}(?:,[0-9]{3})+|[1-9][0-9]*|0)"
        r"\.[0-9]{2}(?![\w$]|[.,][0-9])"
    ),
}


def extract(text: str) -> dict[str, list[str]]:
    """Return matches by category in source order, including duplicates."""
    results = {
        category: [match.group() for match in pattern.finditer(text)]
        for category, pattern in PATTERNS.items()
    }
    # Strip punctuation that usually ends a sentence containing a URL.
    results["urls"] = [url.rstrip(".,;:!?") for url in results["urls"]]
    return results


def validate(category: str, value: str) -> bool:
    """Require the entire value to match the pattern for a known category."""
    return PATTERNS[category].fullmatch(value) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    extraction = commands.add_parser("extract", help="Extract matches as JSON")
    extraction.add_argument("file", nargs="?", default="-", help="UTF-8 file or - for stdin")

    validation = commands.add_parser("validate", help="Check a single field value")
    validation.add_argument("category", choices=PATTERNS)
    validation.add_argument("value")

    args = parser.parse_args()
    if args.command == "validate":
        valid = validate(args.category, args.value)
        print("Valid" if valid else "Invalid")
        return 0 if valid else 1

    try:
        text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        extraction.error(str(error))

    print(json.dumps(extract(text), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
