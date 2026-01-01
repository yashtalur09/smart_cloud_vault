import re

text = """Mumbai, 'INDIA

Date of issue"""

pattern = r'Mumbai[,\s]+(?:\')?INDIA'
m = re.search(pattern, text, re.IGNORECASE)
print(f"Match: {m.group()}")
print(f"lastindex: {m.lastindex}")
print(f"Has groups: {len(m.groups())}")

pob = m.group() if not m.lastindex else m.group(1)
pob = pob.replace("'", "").strip()
print(f"Final POB: {pob}")
