import re

text = """am / Name
Harsh Yadav
'et aTiter / DOB: 06.09.1984

Fe / Male

8108 6494 9408 6584"""

print("Testing pattern matching:")
print()

# Test 12-digit Aadhaar pattern (wrong - Aadhaar is 12 digits not 16!)
pattern1 = r'\d{4}\s*\d{4}\s*\d{4}'
match1 = re.search(pattern1, text)
print(f"Pattern 1 (12 digits): {pattern1}")
print(f"Match: {match1}")
if match1:
    print(f"Found: {match1.group()}")
print()

# Test 16-digit pattern (what we actually have)
pattern2 = r'\d{4}\s*\d{4}\s*\d{4}\s*\d{4}'
match2 = re.search(pattern2, text)
print(f"Pattern 2 (16 digits): {pattern2}")
print(f"Match: {match2}")
if match2:
    print(f"Found: {match2.group()}")
print()

# Count digits in the number
number = "8108 6494 9408 6584"
digits_only = number.replace(" ", "")
print(f"Number: {number}")
print(f"Digits only: {digits_only}")
print(f"Digit count: {len(digits_only)}")
print()

# This is a 16-digit Aadhaar (new format) or possibly Virtual ID
print("NOTE: Standard Aadhaar is 12 digits, but this appears to be 16 digits!")
print("Could be:")
print("  - Virtual ID (VID): 16 digits")
print("  - Masked Aadhaar: XXXX XXXX 6584 (last 4 visible)")
print("  - Or full 16-digit number")
