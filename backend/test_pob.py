import re

text = """Mumbai, 'INDIA"""

patterns = [
    r'Mumbai[,\s]+(?:\')?INDIA',
    r'Mumbai[,\s]+[\'"]?INDIA',
    r'Mumbai.*?INDIA',
]

for p in patterns:
    m = re.search(p, text, re.IGNORECASE)
    print(f"Pattern: {p}")
    print(f"Match: {m.group() if m else 'No match'}")
    print()
