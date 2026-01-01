import re

text = """INCOME TAX DEPARTMENT
GOVT. OF INDIA
Permanent Account Number Card
ABCDE1234F
Name
APPLICANT NAME
Father's Name
APPLICANT'S FATHER NAME
01/06/1995
Signature"""

print("Testing guardian pattern extraction:\n")
print("Text:", repr(text))
print()

# Test current pattern
pattern1 = r"(?:father|mother|guardian|s/o|d/o|w/o|पिता|माता)(?:'s)?\s*(?:name|s\.)?\s*:?\s*\n?\s*([A-Z][A-Z\s]+)(?=\n)"
match1 = re.search(pattern1, text, re.IGNORECASE)
print("Pattern 1 (current):", pattern1[:50] + "...")
print("Match:", match1)
if match1:
    print("Guardian:", match1.group(1))
print()

# Test simpler pattern
pattern2 = r"father'?s?\s+name\s*\n\s*([A-Z][A-Z\s']+)"
match2 = re.search(pattern2, text, re.IGNORECASE)
print("Pattern 2 (simplified):", pattern2)
print("Match:", match2)
if match2:
    print("Guardian:", match2.group(1))
print()

# Test very simple
lines = text.split('\n')
for i, line in enumerate(lines):
    if 'father' in line.lower() and 'name' in line.lower():
        print(f"Found father line at {i}: {line}")
        if i + 1 < len(lines):
            print(f"Next line: {lines[i+1]}")
