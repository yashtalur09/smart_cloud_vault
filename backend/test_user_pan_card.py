"""
Test PAN Card normalization and masking with real OCR output.

This tests the complete flow:
1. OCR extraction (simulated)
2. Classification
3. Normalization
4. Masking
"""

import sys
# Clean reload
for mod in list(sys.modules.keys()):
    if 'ai_engine' in mod:
        del sys.modules[mod]

from ai_engine.context_aware_engine import ContextAwareEngine
from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

# User's actual PAN card OCR (from the issue report)
pan_card_ocr = """INCOME TAX DEPARTMENT
GOVT. OF INDIA
Permanent Account Number Card
ABCDE1234F
Name
APPLICANT NAME
Father's Name
APPLICANT'S FATHER NAME
01/06/1995
Signature"""

print("=" * 80)
print("PAN CARD NORMALIZATION TEST - User's Actual OCR")
print("=" * 80)
print()

print("📄 RAW OCR INPUT:")
print("-" * 80)
print(pan_card_ocr)
print("-" * 80)
print()

# Initialize engines
engine = ContextAwareEngine()
normalizer = GovernmentDocumentNormalizer()

# Step 1: Classify
print("🔍 STEP 1: Classification")
result = engine.process_document(pan_card_ocr, apply_masking=False, preserve_structure=True)
context = result.get('document_context', {})
print(f"   Type: {context.get('type')}")
print(f"   Confidence: {context.get('confidence'):.2%}")
print()

# Step 2: Normalize
print("🔄 STEP 2: Normalization")
normalized = normalizer.normalize_document(pan_card_ocr, context)
print(f"   Document: {normalized.document_type}")
print(f"   Authority: {normalized.authority}")
print(f"   Holder: {normalized.holder_name}")
print(f"   Guardian: {normalized.guardian_name}")
print(f"   DOB: {normalized.date_of_birth}")
print(f"   PAN: {normalized.govt_id_number}")
print(f"   Confidence: {normalized.confidence_score:.2%}")
print()

# Step 3: Format Original (Normalized but Unmasked)
print("📋 STEP 3: Normalized Original (Unmasked)")
print("-" * 80)
normalized_original = normalizer.format_normalized_document(normalized, mask=False)
print(normalized_original)
print("-" * 80)
print()

# Step 4: Format Masked (Normalized and Masked)
print("🔒 STEP 4: Normalized Masked")
print("-" * 80)
normalized_masked = normalizer.format_normalized_document(normalized, mask=True)
print(normalized_masked)
print("-" * 80)
print()

# Verification
print("✅ VERIFICATION:")
print(f"   • Classification: {'✓ government_id' if context.get('type') == 'government_id' else '✗ Failed'}")
print(f"   • Holder Extracted: {'✓' if normalized.holder_name != 'NOT AVAILABLE' else '✗'} ({normalized.holder_name})")
print(f"   • Guardian Extracted: {'✓' if normalized.guardian_name != 'NOT AVAILABLE' else '✗'} ({normalized.guardian_name})")
print(f"   • DOB Extracted: {'✓' if normalized.date_of_birth != 'NOT AVAILABLE' else '✗'} ({normalized.date_of_birth})")
print(f"   • PAN Extracted: {'✓' if normalized.govt_id_number != 'NOT AVAILABLE' else '✗'} ({normalized.govt_id_number})")
print()

# Check masking
has_masked_dob = "[MASKED-DOB]" in normalized_masked
has_masked_pan = "[MASKED-GOVT-ID]" in normalized_masked
has_masked_guardian = "[MASKED-GUARDIAN-NAME]" in normalized_masked

print(f"   • DOB Masked: {'✓' if has_masked_dob else '✗'}")
print(f"   • PAN Masked: {'✓' if has_masked_pan else '✗'}")
print(f"   • Guardian Masked: {'✓' if has_masked_guardian else '✗'}")
print(f"   • Holder NOT Masked: {'✓' if 'APPLICANT NAME' in normalized_masked else '✗'}")
print()

# Final verdict
all_passed = (
    context.get('type') == 'government_id' and
    normalized.holder_name != 'NOT AVAILABLE' and
    normalized.guardian_name != 'NOT AVAILABLE' and
    normalized.date_of_birth != 'NOT AVAILABLE' and
    normalized.govt_id_number != 'NOT AVAILABLE' and
    has_masked_dob and has_masked_pan and has_masked_guardian and
    'APPLICANT NAME' in normalized_masked
)

print("=" * 80)
if all_passed:
    print("✅ ✅ ✅ ALL TESTS PASSED - NORMALIZATION WORKING CORRECTLY ✅ ✅ ✅")
else:
    print("❌ SOME TESTS FAILED - SEE DETAILS ABOVE")
print("=" * 80)
