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

# The actual pattern from the file
pattern = r"(?:father|mother|guardian)['']?s?\s+name\s*\n\s*([A-Z][A-Z\s']+)"

print("Text:")
print(repr(text))
print("\nPattern:")
print(pattern)
print()

# Test with different flags
print("Test 1: IGNORECASE only")
match = re.search(pattern, text, re.IGNORECASE)
print(f"Match: {match}")
if match:
    print(f"Guardian: '{match.group(1)}'")
print()

print("Test 2: IGNORECASE | MULTILINE")
match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
print(f"Match: {match}")
if match:
    print(f"Guardian: '{match.group(1)}'")
print()

print("Test 3: DOTALL")
match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
print(f"Match: {match}")
if match:
    print(f"Guardian: '{match.group(1)}'")
print()

# Check what _is_valid_name would return
def _is_valid_name(name):
    """Validate if string is a valid name."""
    if not name or len(name) < 3:
        print(f"  ❌ Too short: {len(name)}")
        return False
    
    # Must have at least one letter
    if not any(c.isalpha() for c in name):
        print(f"  ❌ No letters")
        return False
    
    # Should not contain numbers
    if any(c.isdigit() for c in name):
        print(f"  ❌ Contains numbers")
        return False
    
    # Should not be common labels or document terms
    exclude_terms = [
        'permanent account number', 'account number', 'card', 'identity',
        'passport', 'license', 'voter', 'aadhaar', 'pan', 'epic',
        'document', 'certificate', 'identification', 'holder name',
        'father name', 'mother name', 'guardian name', 'bearer',
        'signature', 'photo', 'date of birth', 'address'
    ]
    name_lower = name.lower()
    for term in exclude_terms:
        if term in name_lower:
            print(f"  ❌ Excluded term: {term}")
            return False
    
    # Single word labels like "NAME", "FATHER", "SIGNATURE"
    single_labels = ['name', 'father', 'mother', 'guardian', 'holder', 
                    'bearer', 'signature', 'photo', 'address', 'gender']
    if name_lower in single_labels:
        print(f"  ❌ Single label: {name_lower}")
        return False
    
    print(f"  ✅ Valid")
    return True

if match:
    name = match.group(1).strip()
    print(f"\nValidating '{name}':")
    valid = _is_valid_name(name)
    print(f"Result: {valid}")
