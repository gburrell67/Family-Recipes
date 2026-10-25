#!/usr/bin/env python3
"""
add_recipes.py — Import new recipes from an RTF file into the Family Recipes collection.

Usage:
    python3 add_recipes.py [path/to/recipes.rtf]

If no path is given, defaults to: new_recipes.rtf (in the same folder as this script).

RTF File Format
---------------
The script expects one or more recipes in the RTF, separated by a line of
dashes (---) or a blank line between recipes. Each recipe block must contain:

  • A TITLE line  — the first non-blank line (or a line starting with "TITLE:")
  • CATEGORY:     — e.g.  Category: Cakes
  • SOURCE:        — e.g.  Source: Mum          (optional, defaults to "Family")
  • INGREDIENTS:   — starts the ingredient list; one ingredient per line
  • INSTRUCTIONS:  — starts the instruction block; free text until end of block

Minimal example
---------------
    Chocolate Chip Cookies
    Category: Cookies
    Source: Mum

    Ingredients:
    2 cups flour
    1 cup butter
    3/4 cup sugar
    2 eggs
    2 cups chocolate chips

    Instructions:
    Preheat oven to 375°F.
    Mix butter and sugar. Add eggs.
    Fold in flour and chocolate chips.
    Drop by spoonfuls onto baking sheet.
    Bake 10-12 minutes until golden.
    ---

What the script does
--------------------
1. Strips RTF control codes and extracts plain text.
2. Parses each recipe block into title / category / source / ingredients / instructions.
3. Generates a sanitised HTML filename (e.g. "Chocolate Chip Cookies.html").
4. Writes the individual HTML file using the same template as existing recipes.
5. Appends the new recipe entry to recipes.json.
6. Regenerates recipes-data.js from the updated recipes.json.
7. Prints a summary of what was added and skipped.
"""

import os
import re
import json
import sys
import textwrap
from datetime import datetime

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
RECIPES_JSON = os.path.join(SCRIPT_DIR, "recipes.json")
RECIPES_JS   = os.path.join(SCRIPT_DIR, "recipes-data.js")
DEFAULT_RTF  = os.path.join(SCRIPT_DIR, "new_recipes.rtf")

# ── Valid categories (extend as needed) ──────────────────────────────────────
KNOWN_CATEGORIES = {
    "appetizers", "beverages", "breads", "cakes", "cookies", "desserts",
    "main dishes", "muffins", "pies & tarts", "pies and tarts",
    "salads", "squares & bars", "squares and bars", "soups", "sides",
    "condiments", "breakfast", "snacks",
}


# ─────────────────────────────────────────────────────────────────────────────
# RTF → plain text
# ─────────────────────────────────────────────────────────────────────────────

def rtf_to_text(rtf_content: str) -> str:
    """Strip RTF control codes and return plain readable text."""
    text = rtf_content

    # ── Mac TextEdit uses backslash+newline for line breaks ─────────────────
    # e.g.  "Tea Biscuits\<newline>Category: Baking\<newline>"
    # Convert   \<newline>  →  real newline BEFORE stripping control words,
    # so we don't lose the line structure.
    text = re.sub(r'\\\n', '\n', text)

    # Replace common RTF line-break tokens with real newlines
    text = re.sub(r'\\par\b', '\n', text)
    text = re.sub(r'\\line\b', '\n', text)
    text = re.sub(r'\\page\b', '\n', text)
    text = re.sub(r'\\tab\b', '\t', text)

    # Remove destination groups (font tables, colour tables, etc.)
    # Use a loop to handle nested braces
    for _ in range(5):
        text = re.sub(r'\{\\[a-z\*][^{}]{0,300}\}', '', text)

    # Remove hex-encoded characters (\'xx) — keep the visible char where possible
    def decode_hex(m):
        try:
            return bytes([int(m.group(1), 16)]).decode('cp1252', errors='replace')
        except Exception:
            return ''
    text = re.sub(r"\\\'([0-9a-fA-F]{2})", decode_hex, text)

    # Remove all remaining RTF control words/symbols (must come after hex decode)
    text = re.sub(r'\\[a-zA-Z]+[-]?\d*[ ]?', '', text)
    text = re.sub(r'\\\*', '', text)
    text = re.sub(r'[{}]', '', text)   # leftover braces

    # Collapse runs of whitespace (keep newlines)
    lines = [ln.strip() for ln in text.splitlines()]
    # Remove blank-line runs > 1
    cleaned = []
    prev_blank = False
    for ln in lines:
        if ln == '':
            if not prev_blank:
                cleaned.append('')
            prev_blank = True
        else:
            cleaned.append(ln)
            prev_blank = False

    return '\n'.join(cleaned).strip()


# ─────────────────────────────────────────────────────────────────────────────
# Recipe block parser
# ─────────────────────────────────────────────────────────────────────────────

def split_into_blocks(plain_text: str) -> list:
    """Split plain text into individual recipe blocks, skipping the instructions header."""
    # Strip everything up to and including the sentinel line before recipes start.
    # The RTF file uses: "ADD YOUR NEW RECIPES BELOW THIS LINE" as the marker.
    sentinel = re.search(
        r'^ADD YOUR NEW RECIPES BELOW THIS LINE\s*$',
        plain_text, re.MULTILINE | re.IGNORECASE
    )
    if sentinel:
        after = plain_text[sentinel.end():]
        # Also skip any trailing decoration line (===...) immediately after sentinel
        after = re.sub(r'^\s*=+.*\n?', '', after)
        plain_text = after

    # Separator: a line that is only dashes (3+)
    separator = re.compile(r'^-{3,}$', re.MULTILINE)
    raw_blocks = separator.split(plain_text)
    blocks = []
    for block in raw_blocks:
        block = block.strip()
        if block:
            blocks.append(block)
    return blocks


def _strip_label(line: str, *labels) -> tuple:
    """Return (stripped_value, True) if line starts with one of the labels."""
    ll = line.strip()
    for label in labels:
        if ll.lower().startswith(label.lower() + ':'):
            return ll[len(label)+1:].strip(), True
    return ll, False


def parse_block(block: str):
    """
    Parse a single recipe text block into a dict with keys:
        title, category, source, ingredients, instructions
    Returns None if the block doesn't look like a recipe.
    """
    lines = [ln for ln in block.splitlines()]

    # Remove leading/trailing blank lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return None

    recipe = {
        'title': '',
        'category': '',
        'source': 'Family',
        'ingredients': [],
        'instructions': '',
    }

    # State machine
    STATE_HEADER   = 'header'
    STATE_INGR     = 'ingredients'
    STATE_INSTR    = 'instructions'

    state = STATE_HEADER
    title_found = False
    instr_lines = []

    for raw_line in lines:
        line = raw_line.strip()

        # ── Skip empty lines in header ──────────────────────────────────────
        if state == STATE_HEADER and not line:
            continue

        # ── Detect section headers ──────────────────────────────────────────
        ll = line.lower()
        if ll in ('ingredients:', 'ingredients') or ll.startswith('ingredients:'):
            state = STATE_INGR
            # capture inline content after colon
            after = line[len('ingredients'):].lstrip(':').strip()
            if after:
                recipe['ingredients'].append(after)
            continue

        if ll in ('instructions:', 'instructions', 'directions:', 'directions',
                  'method:', 'method', 'instructions & notes:', 'preparation:'):
            state = STATE_INSTR
            after_colon = line.split(':', 1)
            if len(after_colon) > 1 and after_colon[1].strip():
                instr_lines.append(after_colon[1].strip())
            continue

        # ── HEADER section ───────────────────────────────────────────────────
        if state == STATE_HEADER:
            # Title: explicit label or first non-blank, non-meta line
            val, matched = _strip_label(line, 'title', 'recipe', 'recipe name')
            if matched:
                recipe['title'] = val
                title_found = True
                continue

            val, matched = _strip_label(line, 'category', 'cat', 'type')
            if matched:
                recipe['category'] = val
                continue

            val, matched = _strip_label(line, 'source', 'from', 'by', 'author')
            if matched:
                recipe['source'] = val
                continue

            # Unknown header lines — if title not yet set, this is the title
            if not title_found and line:
                recipe['title'] = line
                title_found = True
                continue

            # Otherwise treat as additional meta (could be source/category)
            # last-resort: if line looks like "Source: X"
            if ':' in line:
                key, _, val = line.partition(':')
                key = key.strip().lower()
                val = val.strip()
                if key in ('category', 'cat', 'type'):
                    recipe['category'] = val
                elif key in ('source', 'from', 'by', 'author'):
                    recipe['source'] = val

        # ── INGREDIENTS section ──────────────────────────────────────────────
        elif state == STATE_INGR:
            if line:
                recipe['ingredients'].append(line)

        # ── INSTRUCTIONS section ─────────────────────────────────────────────
        elif state == STATE_INSTR:
            instr_lines.append(line)

    recipe['instructions'] = '\n'.join(instr_lines).strip()

    # ── Validation ───────────────────────────────────────────────────────────
    if not recipe['title']:
        return None
    if not recipe['ingredients'] and not recipe['instructions']:
        return None

    # ── Normalise category ───────────────────────────────────────────────────
    if not recipe['category']:
        recipe['category'] = 'Miscellaneous'

    # Normalise Pies & Tarts / Squares & Bars variants
    cat_norm = {
        'pies and tarts': 'Pies & Tarts',
        'squares and bars': 'Squares & Bars',
    }
    recipe['category'] = cat_norm.get(recipe['category'].lower(), recipe['category'])

    # Title-case category if entirely lower
    if recipe['category'] == recipe['category'].lower():
        recipe['category'] = recipe['category'].title()

    return recipe


# ─────────────────────────────────────────────────────────────────────────────
# ID / filename helpers
# ─────────────────────────────────────────────────────────────────────────────

def title_to_id(title: str) -> str:
    """Convert a recipe title to a URL-safe id (e.g. 'Apple Crunch' → 'apple-crunch')."""
    s = title.lower()
    s = re.sub(r"[''`]", '', s)           # remove apostrophes
    s = re.sub(r'[^a-z0-9]+', '-', s)     # non-alnum → dash
    s = s.strip('-')
    return s


def title_to_filename(title: str) -> str:
    """Derive a clean HTML filename from the title (preserves case)."""
    # Remove characters illegal in filenames
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    safe = safe.strip()
    return f"{safe}.html"


def make_snippet(ingredients: list) -> str:
    """Generate a short ingredient preview snippet."""
    shown = [i.split(',')[0].split('(')[0].strip() for i in ingredients[:4]]
    # Title-case each shown ingredient for display
    shown = [s.title() if s.upper() == s else s for s in shown]
    rest = len(ingredients) - len(shown)
    snippet = ', '.join(shown)
    if rest > 0:
        snippet += f', and {rest} more ingredient{"s" if rest != 1 else ""}...'
    return snippet


# ─────────────────────────────────────────────────────────────────────────────
# HTML generation
# ─────────────────────────────────────────────────────────────────────────────

def escape_html(text: str) -> str:
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def format_instructions_html(instructions: str) -> str:
    """
    If instructions contain numbered steps (1. … 2. …) render as <ol>,
    otherwise render as paragraphs separated by <br> pairs.
    """
    # Detect numbered steps: lines starting with digit + period/dot
    numbered = re.split(r'\n(?=\d+[\.\)]\s)', instructions.strip())
    if len(numbered) > 1:
        items = []
        for step in numbered:
            # Strip leading number
            text = re.sub(r'^\d+[\.\)]\s*', '', step.strip())
            # Bold any "Label:" prefix
            text = re.sub(r'^([A-Z][^:]{2,40}):', r'<strong>\1:</strong>', text)
            items.append(f'          <li>{escape_html_preserve_br(text)}</li>')
        return '        <ol>\n' + '\n'.join(items) + '\n        </ol>'
    else:
        # Paragraph-style
        paras = [p.strip() for p in re.split(r'\n{2,}', instructions.strip()) if p.strip()]
        if len(paras) > 1:
            return '\n'.join(f'        <p>{escape_html(p).replace(chr(10), "<br>")}</p>' for p in paras)
        else:
            lines = [escape_html(ln) for ln in instructions.strip().splitlines()]
            return '        <p>' + '<br>\n        '.join(lines) + '</p>'


def escape_html_preserve_br(text: str) -> str:
    """Escape HTML but keep existing <br> tags (used internally)."""
    text = escape_html(text)
    return text


def build_html(recipe: dict) -> str:
    """Return the full HTML content for a recipe page."""
    title     = escape_html(recipe['title'])
    category  = escape_html(recipe['category'])
    source    = escape_html(recipe['source'])
    desc      = escape_html(recipe['snippet'])

    ingr_items = '\n'.join(
        f'          <li>{escape_html(i)}</li>' for i in recipe['ingredients']
    )

    instr_html = format_instructions_html(recipe['instructions'])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - Heirloom Cookbook</title>
  <meta name="description" content="{desc}">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="recipe-container">
    <nav class="recipe-nav" aria-label="Back navigation">
      <a href="index.html" class="back-link">&larr; Back to Heirloom Cookbook Index</a>
    </nav>

    <header class="recipe-header">
      <span class="category-tag">{category}</span>
      <h1 class="recipe-title">{title}</h1>
      <p class="recipe-source">Source: {source}</p>
    </header>

    <main class="recipe-content">
      <section class="ingredients-section" aria-label="Ingredients">
        <h2>Ingredients</h2>
        <ul>
{ingr_items}
        </ul>
      </section>

      <section class="instructions-section" aria-label="Instructions">
        <h2>Instructions</h2>
{instr_html}
      </section>
    </main>

    <footer class="site-footer">
      <p>Burrell Family Recipes &bull; Heirloom Collection &bull; Handcrafted with love</p>
    </footer>
  </div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# JSON / JS update helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_existing_json() -> list:
    if not os.path.exists(RECIPES_JSON):
        return []
    with open(RECIPES_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(recipes: list):
    with open(RECIPES_JSON, 'w', encoding='utf-8') as f:
        json.dump(recipes, f, indent=2, ensure_ascii=False)
    print(f"  ✅  Updated  {RECIPES_JSON}")


def save_js(recipes: list):
    payload = json.dumps(recipes, indent=2, ensure_ascii=False)
    with open(RECIPES_JS, 'w', encoding='utf-8') as f:
        f.write(f"window.__RECIPES_FALLBACK__ = {payload};\n")
    print(f"  ✅  Updated  {RECIPES_JS}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    rtf_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RTF

    if not os.path.exists(rtf_path):
        print(f"❌  RTF file not found: {rtf_path}")
        sys.exit(1)

    with open(rtf_path, 'r', encoding='utf-8', errors='replace') as f:
        raw = f.read()

    if not raw.strip():
        print(f"⚠️   RTF file is empty: {rtf_path}")
        print("     Add your recipes to the file using the format described in the script header.")
        sys.exit(0)

    # Is it a real RTF file or plain text?
    is_rtf = raw.lstrip().startswith('{\\rtf')
    if is_rtf:
        plain = rtf_to_text(raw)
    else:
        plain = raw   # treat as plain text with the same format

    blocks = split_into_blocks(plain)

    if not blocks:
        print("⚠️   No recipe blocks found in the file.")
        sys.exit(0)

    # Load existing recipes
    existing = load_existing_json()
    existing_ids   = {r['id'] for r in existing}
    existing_files = {r['filename'].lower() for r in existing}

    added   = []
    skipped = []
    errors  = []

    for i, block in enumerate(blocks, 1):
        recipe = parse_block(block)
        if recipe is None:
            skipped.append(f"Block {i}: Could not parse (no title or content found)")
            continue

        # Build derived fields
        recipe['id']       = title_to_id(recipe['title'])
        recipe['filename'] = title_to_filename(recipe['title'])
        recipe['snippet']  = make_snippet(recipe['ingredients'])

        # Check for duplicates
        if recipe['id'] in existing_ids:
            skipped.append(f"'{recipe['title']}' — already exists (id: {recipe['id']})")
            continue
        if recipe['filename'].lower() in existing_files:
            skipped.append(f"'{recipe['title']}' — HTML file already exists ({recipe['filename']})")
            continue

        # Write HTML file
        html_path = os.path.join(SCRIPT_DIR, recipe['filename'])
        if os.path.exists(html_path):
            skipped.append(f"'{recipe['title']}' — HTML file already on disk ({recipe['filename']})")
            continue

        try:
            html_content = build_html(recipe)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            errors.append(f"'{recipe['title']}': Failed to write HTML — {e}")
            continue

        # Build clean entry for JSON (same field order as existing data)
        entry = {
            'id':           recipe['id'],
            'title':        recipe['title'],
            'filename':     recipe['filename'],
            'category':     recipe['category'],
            'source':       recipe['source'],
            'ingredients':  recipe['ingredients'],
            'instructions': recipe['instructions'],
            'snippet':      recipe['snippet'],
        }

        existing.append(entry)
        existing_ids.add(recipe['id'])
        existing_files.add(recipe['filename'].lower())
        added.append(recipe['title'])

    # Sort the full recipe list alphabetically by title
    existing.sort(key=lambda r: r['title'].lower())

    # Save data files only if something was added
    if added:
        save_json(existing)
        save_js(existing)

    # ── Summary ──────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"  Recipe Import Summary — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(f"  Blocks found  : {len(blocks)}")
    print(f"  Added         : {len(added)}")
    print(f"  Skipped       : {len(skipped)}")
    print(f"  Errors        : {len(errors)}")
    print()

    if added:
        print("  ✅  Added recipes:")
        for title in added:
            print(f"       • {title}")
        print()

    if skipped:
        print("  ⏭️   Skipped:")
        for msg in skipped:
            print(f"       • {msg}")
        print()

    if errors:
        print("  ❌  Errors:")
        for msg in errors:
            print(f"       • {msg}")
        print()

    if not added and not errors:
        print("  ℹ️   Nothing new was added.")
    print("=" * 60)


if __name__ == '__main__':
    main()
