"""Test Aadhaar normalization with user's actual OCR."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Force clean reload
for mod in list(sys.modules.keys()):
    if 'ai_engine' in mod:
        del sys.modules[mod]

from ai_engine.context_aware_engine import ContextAwareEngine
from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

# User's actual Aadhaar OCR
aadhaar_ocr = """am / Name
Harsh Yadav
'et aTiter / DOB: 06.09.1984

Fe / Male

8108 6494 9408 6584"""

print("=" * 80)
print("AADHAAR CARD NORMALIZATION TEST - User's Actual OCR")
print("=" * 80)
print()

print("📄 RAW OCR INPUT:")
print("-" * 80)
print(aadhaar_ocr)
print("-" * 80)
print()

# Initialize engines
engine = ContextAwareEngine()
normalizer = GovernmentDocumentNormalizer()

# Step 1: Classify
print("🔍 STEP 1: Classification")
result = engine.process_document(aadhaar_ocr, apply_masking=False, preserve_structure=True)
context = result.get('document_context', {})
print(f"   Type: {context.get('type')}")
print(f"   Confidence: {context.get('confidence'):.2%}")
print(f"   Keywords: {context.get('keywords')[:5] if context.get('keywords') else []}")
print()

# Check if it's classified as government_id
if context.get('type') != 'government_id':
    print("❌ NOT CLASSIFIED AS GOVERNMENT_ID!")
    print("   This is why normalization isn't happening.")
    print()
else:
    print("✅ Correctly classified as government_id")
    print()

# Step 2: Try normalization anyway
print("🔄 STEP 2: Normalization (forced)")
try:
    normalized = normalizer.normalize_document(aadhaar_ocr, context)
    print(f"   Document: {normalized.document_type}")
    print(f"   Authority: {normalized.authority}")
    print(f"   Holder: {normalized.holder_name}")
    print(f"   DOB: {normalized.date_of_birth}")
    print(f"   Gender: {normalized.gender}")
    print(f"   Aadhaar: {normalized.govt_id_number}")
    print(f"   Confidence: {normalized.confidence_score:.2%}")
    print()
    
    # Step 3: Format Original
    print("📋 STEP 3: Normalized Original")
    print("-" * 80)
    normalized_original = normalizer.format_normalized_document(normalized, mask=False)
    print(normalized_original)
    print("-" * 80)
    print()
    
    # Step 4: Format Masked
    print("🔒 STEP 4: Normalized Masked")
    print("-" * 80)
    normalized_masked = normalizer.format_normalized_document(normalized, mask=True)
    print(normalized_masked)
    print("-" * 80)
    print()
    
except Exception as e:
    print(f"❌ Normalization failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
