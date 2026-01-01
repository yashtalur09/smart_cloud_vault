import re

text = """am / Name
Harsh Yadav
'et aTiter / DOB: 06.09.1984

Fe / Male

8108 6494 9408 6584"""

print("Testing Aadhaar number extraction:")
print()

# Original pattern (12 digits only)
pattern1 = r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b'
match1 = re.search(pattern1, text)
print(f"Pattern 1 (12 digits): {pattern1}")
print(f"Match: {match1}")
if match1:
    print(f"ID: {match1.group(1)}")
print()

# New pattern (12 or 16 digits)
pattern2 = r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?:[\s\-]?\d{4})?)\b'
match2 = re.search(pattern2, text)
print(f"Pattern 2 (12 or 16 digits): {pattern2}")
print(f"Match: {match2}")
if match2:
    print(f"ID: {match2.group(1)}")
print()

# Try without word boundaries
pattern3 = r'(\d{4}\s+\d{4}\s+\d{4}(?:\s+\d{4})?)'
match3 = re.search(pattern3, text)
print(f"Pattern 3 (no word boundaries): {pattern3}")
print(f"Match: {match3}")
if match3:
    print(f"ID: {match3.group(1)}")
print()

# Check what's around the number
import re
lines = text.split('\n')
for i, line in enumerate(lines):
    if '8108' in line:
        print(f"Line {i}: {repr(line)}")
        print(f"Previous: {repr(lines[i-1]) if i > 0 else 'None'}")
        print(f"Next: {repr(lines[i+1]) if i < len(lines)-1 else 'None'}")
