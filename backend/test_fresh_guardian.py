import re
import sys
import importlib

# Force reload the normalizer module
if 'ai_engine.govt_doc_normalizer' in sys.modules:
    del sys.modules['ai_engine.govt_doc_normalizer']

from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

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

normalizer = GovernmentDocumentNormalizer()

print("Testing updated GUARDIAN_PATTERNS:")
print("Patterns:", normalizer.GUARDIAN_PATTERNS)
print()

for i, pattern in enumerate(normalizer.GUARDIAN_PATTERNS, 1):
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    print(f"Pattern {i}: {pattern[:60]}...")
    if match:
        print(f"  ✅ Match: {match.group(0)}")
        print(f"  Guardian: {match.group(1)}")
    else:
        print("  ❌ No match")
    print()
