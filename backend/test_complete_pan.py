import sys
# Force clean reload
for mod in list(sys.modules.keys()):
    if 'ai_engine' in mod:
        del sys.modules[mod]

from ai_engine.context_aware_engine import ContextAwareEngine
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

print("🔍 Testing Complete PAN Card Normalization\n")

engine = ContextAwareEngine()
normalizer = GovernmentDocumentNormalizer()

# Step 1: Classification
result = engine.process_document(text, apply_masking=False, preserve_structure=True)
context = result.get('document_context', {})

print(f"1️⃣  Classification: {context.get('type')}")
print(f"   Confidence: {context.get('confidence'):.2%}\n")

# Step 2: Normalization
normalized = normalizer.normalize_document(text, context)

print("2️⃣  Extracted Fields:")
print(f"   Holder: {normalized.holder_name}")
print(f"   Guardian: {normalized.guardian_name}")
print(f"   DOB: {normalized.date_of_birth}")
print(f"   PAN: {normalized.govt_id_number}\n")

# Step 3: Format masked
masked = normalizer.format_normalized_document(normalized, mask=True)

print("3️⃣  Masked Output:")
print(masked)
print("\n✅ COMPLETE!" if normalized.guardian_name != "NOT AVAILABLE" else "\n❌ Guardian extraction failed")
