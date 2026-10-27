#!/usr/bin/env python3
"""
fix_caps.py - convert ALL-CAPS recipe text to proper capitalization.

  Ingredients  ->  "2 CUPS FLOUR"      becomes  "2 cups Flour"
                   "1 TBSP. BAKING SODA" becomes "1 Tbsp. Baking Soda"
  Instructions ->  sentence case, e.g. "BAKE 350 FOR 1 HOUR." -> "Bake 350 for 1 hour."

Only lines that are mostly upper-case are touched; lines that are already
mixed-case are left alone. Safe to re-run.

Usage:
    python3 fix_caps.py           # dry run: show a sample of changes
    python3 fix_caps.py --apply   # rewrite recipes.json, recipes-data.js and the HTML pages
"""
import glob
import json
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))

UNITS = {'cup', 'cups', 'tsp', 'tsp.', 'tbsp', 'tbsp.', 'lb', 'lb.', 'lbs', 'lbs.', 'oz', 'oz.',
         'pkg', 'pkg.', 'pkgs.', 'qt', 'qt.', 'pt', 'pt.', 'ml', 'g', 'kg', 'c', 'c.', 't', 't.',
         'min', 'mins', 'min.', 'mins.', 'hr', 'hr.', 'hrs', 'hrs.', 'pinch', 'dash', 'can', 'cans'}
SMALL = {'a', 'an', 'and', 'or', 'of', 'to', 'for', 'in', 'on', 'with', 'the', 'at', 'by', 'from', 'as', 'into'}
# size / preparation words kept lower-case in ingredient lines ("1 large Onion", "Butter melted")
DESCRIPTORS = {'large', 'medium', 'small', 'chopped', 'melted', 'softened', 'beaten', 'sifted', 'grated',
               'sliced', 'diced', 'minced', 'crushed', 'packed', 'divided', 'finely', 'fresh', 'frozen',
               'optional', 'well', 'drained', 'thawed', 'cooked', 'uncooked', 'whole', 'heaping', 'level'}
# a line starting with one of these continues the previous line's sentence
CONTINUATION = {'in', 'and', 'or', 'of', 'to', 'with', 'the', 'a', 'an', 'until', 'over', 'for', 'on',
                'at', 'into', 'then,', 'but', 'by', 'from', 'as', 'is', 'are', 'it', 'its', 'that', 'which',
                'about', 'add', 'minutes', 'mins', 'min', 'hour', 'hours', 'cup', 'cups', 'tsp', 'tbsp'}
# abbreviations whose trailing period does NOT end a sentence
ABBREV = {'tsp', 'tbsp', 'lb', 'lbs', 'oz', 'pkg', 'pkgs', 'qt', 'pt', 'min', 'mins', 'hr', 'hrs',
          'approx', 'c', 'mrs', 'mr', 'dr', 'sq', 'doz', 'no', 'choc'}
PROPER = {'dijon': 'Dijon', 'smarties': 'Smarties', 'tobasco': 'Tobasco', 'worchester': 'Worchester',
          'worcestershire': 'Worcestershire', 'worchestershire': 'Worcestershire',
          'jell-o': 'Jell-O', 'jello': 'Jell-O', 'ritz': 'Ritz', 'crisco': 'Crisco',
          'bisquick': 'Bisquick', 'miracle': 'Miracle', 'whip': 'Whip', 'cool': 'Cool',
          'dutch': 'Dutch', 'special': 'Special', 'nabisco': 'Nabisco', 'rice': 'Rice',
          'krispies': 'Krispies', 'graham': 'Graham', 'french': 'French', 'english': 'English',
          'canadian': 'Canadian', 'american': 'American', 'cheddar': 'Cheddar',
          'parmesan': 'Parmesan', 'swiss': 'Swiss', 'philadelphia': 'Philadelphia',
          'saltpetre': 'Saltpetre', 'nana\'s': "Nana's", "mum's": "Mum's"}


def is_caps(s: str) -> bool:
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 3 and sum(c.isupper() for c in letters) / len(letters) > 0.6


def _fix_temps(s: str) -> str:
    # "350 f" / "350 F" / "350°f" -> "350°F"
    return re.sub(r'\b(\d{3})\s*°?\s*([fFcC])\b(?!\w)', lambda m: f"{m.group(1)}°{m.group(2).upper()}", s)


def fix_ingredient(line: str) -> str:
    if re.match(r'^-{2,3}.+-{2,3}$', line.strip()) or not is_caps(line):
        return line
    text = _fix_temps(line.lower())
    out = []
    depth = 0
    for tok in re.split(r'(\s+)', text):
        if not tok or tok.isspace():
            out.append(tok)
            continue
        opens, closes = tok.count('('), tok.count(')')
        in_paren = depth > 0 or opens > 0
        depth += opens - closes
        core = tok.strip('(),;:')
        if in_paren:                       # keep parenthetical notes lower-case
            out.append(tok)
            continue
        if core in ('tbsp.', 'tbsp'):
            out.append(tok.replace('tbsp', 'Tbsp'))
        elif core in UNITS or re.match(r'^[\d/.\-]+$', core) or '°' in core:
            out.append(tok)
        elif core in PROPER:
            out.append(tok.replace(core, PROPER[core]))
        elif core in DESCRIPTORS or (core in SMALL and out and any(p.strip() for p in out)):
            out.append(tok)
        else:
            out.append(re.sub(r'[a-z]', lambda m: m.group(0).upper(), tok, count=1) if tok[0].isalpha() or tok[0] in "('\"" else tok)
    res = ''.join(out)
    # capitalise first alphabetic character of the line (e.g. "Salt and Pepper...")
    for i, c in enumerate(res):
        if c.isalpha():
            res = res[:i] + c.upper() + res[i + 1:]
            break
        if c.isdigit():
            break
    return res


def fix_instruction_line(line: str) -> str:
    if not is_caps(line):
        return line
    text = _fix_temps(line.lower())
    text = re.sub(r'\bi\b', 'I', text)
    for k, v in PROPER.items():
        text = re.sub(r'\b' + re.escape(k) + r'\b', v, text)
    text = re.sub(r'\b(tbsp)\b', 'Tbsp', text)

    def cap_after(m):
        before = text[:m.start()].split()
        prev = before[-1].lower().strip('()') if before else ''
        if m.group(1) == '.' and (prev in ABBREV or any(ch.isdigit() for ch in prev) or len(prev) == 1):
            return m.group(0)
        return m.group(1) + m.group(2) + m.group(3).upper()
    text = re.sub(r'([.!?])(\s+)([a-z])', cap_after, text)
    # a new line starts a new step, unless it just continues the previous sentence
    def cap_line(m):
        if m.group(2).split(' ')[0].split('-')[0] in CONTINUATION:
            return m.group(0)
        return m.group(1) + m.group(2)[0].upper() + m.group(2)[1:]
    text = re.sub(r'(\n\s*)([a-z][^\s]*)', cap_line, text)
    # capitalise the first letter of the line (unless the line starts with a number)
    m = re.search(r'[a-z]', text)
    if m and not text.lstrip()[:1].isdigit():
        text = text[:m.start()] + text[m.start()].upper() + text[m.start() + 1:]
    return text


def fix_instructions(text: str) -> str:
    # Convert as one block so a line break in the middle of a sentence does not
    # start a new capital letter; only real sentence ends do.
    if is_caps(text):
        return fix_instruction_line(text)
    return '\n'.join(fix_instruction_line(l) for l in text.split('\n'))


# ----------------------------------------------------------------- HTML
def fix_html(html: str) -> str:
    def li(m):
        inner = m.group(2)
        return m.group(1) + fix_ingredient(inner) + m.group(3)
    html = re.sub(r'(<li>)(.*?)(</li>)', li, html)

    def instr(m):
        parts = m.group(2).split('<br>')
        return m.group(1) + '<br>'.join(fix_instructions('\n'.join(parts)).split('\n')) + m.group(3)
    html = re.sub(r'(<div class="instructions">)(.*?)(</div>)', instr, html, flags=re.S)
    return html


def main():
    apply = '--apply' in sys.argv
    path = os.path.join(DIR, 'recipes.json')
    data = json.load(open(path, encoding='utf-8'))
    changed = 0
    for r in data:
        new_ing = [fix_ingredient(i) for i in r['ingredients']]
        new_ins = fix_instructions(r['instructions'])
        if new_ing != r['ingredients'] or new_ins != r['instructions']:
            changed += 1
            if not apply and changed <= 4:
                print(f"== {r['title']}")
                for a, b in list(zip(r['ingredients'], new_ing))[:6]:
                    print(f"   {a!r:45} -> {b!r}")
                print(f"   INSTR: {r['instructions'][:140]!r}\n      ->  {new_ins[:140]!r}\n")
            r['ingredients'], r['instructions'] = new_ing, new_ins
            # refresh the index snippet from the corrected ingredients
            real = [i for i in new_ing if not re.match(r'^-{2,3}.+-{2,3}$', i.strip())]
            shown = [i.split(',')[0].split('(')[0].strip() for i in real[:4]]
            rest = len(real) - len(shown)
            r['snippet'] = ', '.join(shown) + (f", and {rest} more ingredient{'s' if rest != 1 else ''}..." if rest > 0 else '')
    print(f"{changed} recipes would change" if not apply else f"{changed} recipes updated")
    if not apply:
        return
    json.dump(data, open(path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    with open(os.path.join(DIR, 'recipes-data.js'), 'w', encoding='utf-8') as f:
        f.write('window.__RECIPES_FALLBACK__ = ' + json.dumps(data, indent=2, ensure_ascii=False) + ';\n')
    n = 0
    for p in glob.glob(os.path.join(DIR, '*.html')):
        if os.path.basename(p) == 'index.html':
            continue
        h = open(p, encoding='utf-8', newline='').read()
        new = fix_html(h)
        if new != h:
            open(p, 'w', encoding='utf-8', newline='').write(new)
            n += 1
    print(f"{n} HTML pages updated")


if __name__ == '__main__':
    main()
