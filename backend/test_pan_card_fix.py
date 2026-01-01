"""Test script to verify PAN card OCR improvements and proper masking."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.ocr_processor import ocr_processor
from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer
from ai_engine.context_aware_engine import context_engine

def test_pan_card_extraction():
    """Test PAN card extraction with improved OCR."""
    
    print("=" * 80)
    print("PAN CARD OCR & MASKING TEST")
    print("=" * 80)
    
    # Sample noisy OCR text (simulating what we get from the uploaded image)
    noisy_ocr_text = """ARMA URIS
GOVT. OF INDIA

Stree feast

"OUMETA DEPARTMENT fe
wrt der wer 7 oe

~ Permanent Account Number Card

RS BQUPY0939B

TALUR YASHWANTH

5

frat a1 7 / Father's Name | oe ees
TALUR NATASHEKAR so a

wa wi atte / D:
09/01/2006. Fann / Signature 9554237"""
    
    print("\n1. INPUT - Noisy OCR Text:")
    print("-" * 80)
    print(noisy_ocr_text)
    print("-" * 80)
    
    # Test with context-aware engine
    print("\n2. Processing with context-aware engine...")
    result = context_engine.process_document(
        text=noisy_ocr_text,
        apply_masking=False,
        preserve_structure=True
    )
    
    document_context = result.get('document_context', {})
    print(f"\nDocument Type: {document_context.get('type')}")
    print(f"Confidence: {document_context.get('confidence', 0):.2%}")
    print(f"Keywords: {document_context.get('keywords', [])}")
    
    # Test normalization
    print("\n3. Normalizing document...")
    normalizer = GovernmentDocumentNormalizer()
    normalized_doc = normalizer.normalize_document(noisy_ocr_text, document_context)
    
    print(f"\nNormalized Document Type: {normalized_doc.document_type}")
    print(f"Authority: {normalized_doc.authority}")
    print(f"Overall Confidence: {normalized_doc.confidence_score:.2%}")
    print("\nExtracted Fields:")
    print(f"  - Holder Name: {normalized_doc.holder_name} (conf: {normalized_doc.field_confidences.get('holder_name', 0):.2%})")
    print(f"  - PAN Number: {normalized_doc.govt_id_number} (conf: {normalized_doc.field_confidences.get('govt_id_number', 0):.2%})")
    print(f"  - DOB: {normalized_doc.date_of_birth} (conf: {normalized_doc.field_confidences.get('date_of_birth', 0):.2%})")
    print(f"  - Father's Name: {normalized_doc.guardian_name} (conf: {normalized_doc.field_confidences.get('guardian_name', 0):.2%})")
    
    # Generate formatted output (unmasked)
    print("\n4. UNMASKED OUTPUT:")
    print("=" * 80)
    unmasked_text = normalizer.format_normalized_document(
        normalized_doc,
        mask=False,
        raw_text=noisy_ocr_text
    )
    print(unmasked_text)
    print("=" * 80)
    
    # Generate formatted output (masked)
    print("\n5. MASKED OUTPUT:")
    print("=" * 80)
    masked_text = normalizer.format_normalized_document(
        normalized_doc,
        mask=True,
        raw_text=noisy_ocr_text
    )
    print(masked_text)
    print("=" * 80)
    
    # Verify masking worked
    print("\n6. VERIFICATION:")
    print("-" * 80)
    
    has_dob_in_masked = "09/01/2006" in masked_text or "09/01/2006" in masked_text
    has_father_in_masked = "TALUR NATASHEKAR" in masked_text or "NATASHEKAR" in masked_text
    has_masked_dob = "[MASKED-DOB]" in masked_text
    has_masked_father = "[MASKED-FATHER-NAME]" in masked_text
    
    print(f"✓ Unmasked contains PAN: {'BQUPY0939B' in unmasked_text}")
    print(f"✓ Unmasked contains Name: {'YASHWANTH' in unmasked_text or 'TALUR' in unmasked_text}")
    print(f"✓ Unmasked contains DOB: {'09/01/2006' in unmasked_text}")
    print(f"✓ Unmasked contains Father: {'NATASHEKAR' in unmasked_text or 'TALUR' in unmasked_text}")
    
    print(f"\n✓ Masked contains PAN: {'BQUPY0939B' in masked_text}")
    print(f"✓ Masked contains Name: {'YASHWANTH' in masked_text or 'TALUR' in masked_text}")
    print(f"✗ Masked hides DOB: {has_masked_dob and not has_dob_in_masked}")
    print(f"✗ Masked hides Father: {has_masked_father and not has_father_in_masked}")
    
    # Summary
    print("\n" + "=" * 80)
    if has_masked_dob and has_masked_father:
        print("✅ SUCCESS: Masking is working correctly!")
        print("   - Sensitive fields (DOB, Father's Name) are properly masked")
        print("   - Non-sensitive fields (Name, PAN) remain visible")
    else:
        print("⚠️  WARNING: Masking may not be complete")
        if not has_masked_dob:
            print("   - DOB was not masked")
        if not has_masked_father:
            print("   - Father's name was not masked")
    print("=" * 80)
    
    return normalized_doc, unmasked_text, masked_text

if __name__ == "__main__":
    try:
        test_pan_card_extraction()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
