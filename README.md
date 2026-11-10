# Regex Data Extraction

This Python project extracts eight kinds of data from mixed text and validates individual values. It uses the same compiled regular expressions for both tasks. Extraction returns each category as a JSON list, in the order the matches appear in the input. Repeated matches are kept, and categories with no matches get empty lists.

## Setup

Use Python 3.10 or newer. The project uses only the Python standard library.

```sh
git clone https://github.com/Ebenezer-Kofi-Annan/alu_regex-data-extraction-Ebenezer-Kofi-Annan.git
cd alu_regex-data-extraction-Ebenezer-Kofi-Annan
python regex_extractor.py extract samples/mixed.txt
```

You can pass a UTF-8 text file or pipe text into `extract`.

```sh
echo "Contact user@example.com at 14:30." | python regex_extractor.py extract
```

Use `validate` to check one complete field value. Quote values that contain spaces. The command prints `Valid` and exits with code `0` for a match, or prints `Invalid` and exits with code `1` for a format mismatch.

```sh
python regex_extractor.py validate times "2:30 PM"
python regex_extractor.py validate times "24:00"
```

Python callers can import `extract(text)` and `validate(category, value)` from `regex_extractor`.

## Supported formats

| Category | Supported examples | Matching rules |
| --- | --- | --- |
| `emails` | `user@example.com`, `firstname.lastname@company.co.uk` | Dot-separated local parts and dotted ASCII domains. Consecutive dots in the local part and leading or trailing domain-label hyphens are rejected. |
| `urls` | `https://www.example.com`, `https://subdomain.example.org/page` | HTTP and HTTPS with a dotted ASCII domain, an optional 1–5 digit port, and optional path, query, and fragment. Percent escapes require two hexadecimal digits. Extraction strips trailing sentence punctuation. |
| `phones` | `(123) 456-7890`, `123-456-7890`, `123.456.7890`, `123 456 7890` | Ten-digit numbers in these formats. The plain three-group form uses a consistent separator. |
| `credit_cards` | `1234 5678 9012 3456`, `1234-5678-9012-3456` | Four groups of four digits with consistent spaces or hyphens. Validation checks the format only. |
| `times` | `14:30`, `2:30 PM`, `00:00` | Two-digit hours from `00` to `23` in 24-hour time, or hours from `1` to `12` with a case-insensitive `AM` or `PM`. Minutes range from `00` to `59`. |
| `html_tags` | `<p>`, `<div class="example">`, `</div>`, `<br />` | Opening, closing, and self-closing tags. Attributes can be boolean or take quoted or unquoted values. Matches are individual tags. |
| `hashtags` | `#example`, `#ThisIsAHashtag`, `#café` | A `#` followed by one or more Unicode word characters. The pattern skips tags attached to preceding words and common URL delimiters. |
| `currencies` | `$19.99`, `$1,234.56`, `$0.00` | Unsigned dollar amounts with exactly two decimal places and optional comma grouping in thousands. |

Extraction uses `re.finditer()` to collect full matches within text. Lookarounds help avoid extracting fragments of malformed values. Field validation uses `re.fullmatch()` and treats surrounding whitespace as part of the value. These patterns recognize common formats for the assignment, with narrower coverage than full email, URL, and HTML specifications.

## Sample output

The [sample input](samples/mixed.txt) includes valid formats and malformed examples. Running `python regex_extractor.py extract samples/mixed.txt` produces:

```json
{
  "emails": ["user@example.com", "firstname.lastname@company.co.uk"],
  "urls": ["https://www.example.com", "https://subdomain.example.org/page"],
  "phones": ["(123) 456-7890", "123-456-7890", "123.456.7890"],
  "credit_cards": ["1234 5678 9012 3456", "1234-5678-9012-3456"],
  "times": ["14:30", "2:30 PM"],
  "html_tags": ["<p>", "<div class=\"example\">", "<img src=\"image.jpg\" alt=\"description\">"],
  "hashtags": ["#example", "#ThisIsAHashtag"],
  "currencies": ["$19.99", "$1,234.56"]
}
```

## Tests

```sh
python -m unittest discover -s tests -v
```

The tests cover the assignment examples, alternative formats, partial matches in malformed text, repeated matches, punctuation, and command-line behavior.
