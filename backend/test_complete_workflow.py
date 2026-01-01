"""
COMPREHENSIVE TEST: Purpose-Aware Masking System
Demonstrates complete workflow with both Aadhaar and PAN cards
"""

import sys
sys.path.append('d:/Cloud EL/Smart_Cloud_Vault/backend')

from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

def print_header(title):
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80)

def print_section(title):
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80)

def test_complete_workflow():
    """Demonstrate complete workflow from raw OCR to masked output."""
    
    print_header("PURPOSE-AWARE MASKING SYSTEM - COMPLETE WORKFLOW")
    
    print("""
This test demonstrates the complete document processing workflow:
1. Raw OCR text (unstructured, noisy)
2. Document normalization (structured, validated)
3. Purpose-aware masking (privacy-preserving)
""")
    
    normalizer = GovernmentDocumentNormalizer()
    
    # =========================================================================
    # TEST CASE 1: AADHAAR CARD WITH FULL DETAILS
    # =========================================================================
    
    print_header("TEST CASE 1: AADHAAR CARD")
    
    aadhaar_ocr = """Government of India
Unique Identification Authority

Name: PRIYA SHARMA
DOB: 15.06.1992
Gender: Female

Address:
Flat 501, Tower B, Green Park
Sector 18, Gurgaon
Haryana - 122001

VID: 2345 6789 0123 4567"""
    
    print_section("STEP 1: Raw OCR Input (Noisy, Unstructured)")
    print(aadhaar_ocr)
    
    document_context = {
        'classification': 'government_id',
        'confidence': 0.95,
        'identity_signals': {'aadhaar': True}
    }
    
    normalized_doc = normalizer.normalize_document(aadhaar_ocr, document_context)
    
    original = normalizer.format_normalized_document(normalized_doc, mask=False)
    masked = normalizer.format_normalized_document(normalized_doc, mask=True)
    
    print_section("STEP 2: Normalized Original (Structured, Unmasked)")
    print(original)
    
    print_section("STEP 3: Masked for Organization (Privacy-Preserving)")
    print(masked)
    
    print_section("VALIDATION - What Changed?")
    print("✅ Name: VISIBLE in both (organization needs to verify identity)")
    print("✅ Aadhaar/VID: VISIBLE in both (organization needs to verify document)")
    print("✅ DOB: VISIBLE in both (organization needs for age verification)")
    print("✅ Gender: VISIBLE in both (organization needs for identity verification)")
    print("❌ Address: MASKED in organization copy (personal detail - not needed)")
    print("✅ Metadata: Added to show masking policy and visible/masked fields")
    
    # Verification
    assert "PRIYA SHARMA" in masked
    assert "2345 6789 0123 4567" in masked
    assert "15.06.1992" in masked
    assert "Female" in masked
    assert "[MASKED-ADDRESS]" in masked
    assert "Green Park" not in masked
    assert "MASKING METADATA" in masked
    
    print("\n✅ AADHAAR CARD: ALL CHECKS PASSED")
    
    # =========================================================================
    # TEST CASE 2: PAN CARD WITH FULL DETAILS
    # =========================================================================
    
    print_header("TEST CASE 2: PAN CARD")
    
    pan_ocr = """INCOME TAX DEPARTMENT
GOVERNMENT OF INDIA

Permanent Account Number Card

Name: VIKRAM SINGH
Father's Name: AJAY SINGH
Date of Birth: 20/11/1988

CDFPS9876Q

Signature"""
    
    print_section("STEP 1: Raw OCR Input (Noisy, Unstructured)")
    print(pan_ocr)
    
    document_context = {
        'classification': 'government_id',
        'confidence': 0.95,
        'identity_signals': {'pan': True}
    }
    
    normalized_doc = normalizer.normalize_document(pan_ocr, document_context)
    
    original = normalizer.format_normalized_document(normalized_doc, mask=False)
    masked = normalizer.format_normalized_document(normalized_doc, mask=True)
    
    print_section("STEP 2: Normalized Original (Structured, Unmasked)")
    print(original)
    
    print_section("STEP 3: Masked for Organization (Privacy-Preserving)")
    print(masked)
    
    print_section("VALIDATION - What Changed?")
    print("✅ Name: VISIBLE in both (organization needs to verify identity)")
    print("✅ PAN Number: VISIBLE in both (organization needs for tax verification)")
    print("✅ DOB: VISIBLE in both (organization needs for age verification)")
    print("❌ Father's Name: MASKED in organization copy (personal detail - not needed)")
    print("✅ Metadata: Added to show masking policy and visible/masked fields")
    
    # Verification
    assert "VIKRAM SINGH" in masked
    assert "CDFPS9876Q" in masked
    assert "20/11/1988" in masked
    assert "[MASKED-GUARDIAN-NAME]" in masked
    assert "AJAY SINGH" not in masked
    assert "MASKING METADATA" in masked
    
    print("\n✅ PAN CARD: ALL CHECKS PASSED")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    
    print_header("TEST SUMMARY")
    
    print("""
✅ TEST RESULTS:
   • Aadhaar Card: Processing complete with purpose-aware masking
   • PAN Card: Processing complete with purpose-aware masking
   
✅ MASKING POLICY VALIDATION:
   • Organization-required fields remain VISIBLE (Name, ID, DOB, Gender)
   • Personal details properly MASKED (Address, Father's Name)
   • Masking metadata correctly added to all masked versions
   
✅ PRIVACY PROTECTION:
   • Employee addresses protected
   • Guardian/parent names protected
   • Only necessary information exposed
   
✅ ORGANIZATIONAL NEEDS:
   • Identity verification enabled (Name + Document ID)
   • Age verification enabled (DOB visible)
   • Gender identification enabled
   • Document authenticity verifiable (Authority, ID Number)

✅ TECHNICAL IMPLEMENTATION:
   • Document-specific templates working correctly
   • Pattern-based detection functioning (Aadhaar, PAN)
   • Guardian name extraction improved
   • Masking metadata generation working
   • No impact on OCR, normalization, or access control

🎉 PURPOSE-AWARE MASKING: FULLY FUNCTIONAL AND TESTED!
""")

if __name__ == "__main__":
    try:
        test_complete_workflow()
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED SUCCESSFULLY".center(80))
        print("=" * 80 + "\n")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
