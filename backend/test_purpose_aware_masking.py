"""Test purpose-aware masking policy for Aadhaar and PAN cards."""

import sys
sys.path.append('d:/Cloud EL/Smart_Cloud_Vault/backend')

from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

def test_aadhaar_masking():
    """Test Aadhaar card with purpose-aware masking."""
    
    print("=" * 80)
    print("TEST 1: AADHAAR CARD - PURPOSE-AWARE MASKING")
    print("=" * 80)
    
    # Sample Aadhaar OCR from user's actual card
    aadhaar_ocr = """am / Name
Harsh Yadav
'et aTiter / DOB: 06.09.1984

Fe / Male

8108 6494 9408 6584"""
    
    normalizer = GovernmentDocumentNormalizer()
    
    # Create document context (simulating what classifier provides)
    document_context = {
        'classification': 'government_id',
        'confidence': 0.95,
        'identity_signals': {'aadhaar': True}
    }
    
    # Normalize the document
    normalized_doc = normalizer.normalize_document(aadhaar_ocr, document_context)
    
    # Get original (unmasked) formatted text
    original_text = normalizer.format_normalized_document(normalized_doc, mask=False)
    
    # Get masked formatted text
    masked_text = normalizer.format_normalized_document(normalized_doc, mask=True)
    
    print("\n📄 ORIGINAL (Unmasked):")
    print("-" * 80)
    print(original_text)
    print("-" * 80)
    
    print("\n🔒 MASKED (Purpose-Aware):")
    print("-" * 80)
    print(masked_text)
    print("-" * 80)
    
    # Validation
    print("\n✅ VALIDATION:")
    
    # Check what SHOULD be visible
    checks = {
        "✅ Name visible (Harsh Yadav)": "Harsh Yadav" in masked_text,
        "✅ Aadhaar Number visible": "8108 6494 9408 6584" in masked_text,
        "✅ DOB visible (06.09.1984)": "06.09.1984" in masked_text and "[MASKED-DOB]" not in masked_text,
        "✅ Gender visible (Male)": "Male" in masked_text and "[MASKED-GENDER]" not in masked_text,
        "✅ Address properly masked": "[MASKED-ADDRESS]" in masked_text or "NOT AVAILABLE" in masked_text,
        "✅ Masking metadata present": "MASKING METADATA" in masked_text,
        "✅ Policy is organizational_use": "organizational_use" in masked_text,
    }
    
    for check, passed in checks.items():
        symbol = "✅" if passed else "❌"
        print(f"   {symbol} {check}")
    
    all_passed = all(checks.values())
    if all_passed:
        print("\n🎉 AADHAAR PURPOSE-AWARE MASKING: WORKING PERFECTLY!")
    else:
        print("\n⚠️  Some checks failed!")
    
    return all_passed


def test_pan_masking():
    """Test PAN card with purpose-aware masking."""
    
    print("\n\n" + "=" * 80)
    print("TEST 2: PAN CARD - PURPOSE-AWARE MASKING")
    print("=" * 80)
    
    # Sample PAN OCR from user's actual card (with actual father's name)
    pan_ocr = """INCOME TAX DEPARTMENT
GOVT. OF INDIA

Permanent Account Number
ABCDE1234F

Name: RAMESH KUMAR
Father's Name: VIJAY KUMAR
Date of Birth: 15/08/1990

Signature"""
    
    normalizer = GovernmentDocumentNormalizer()
    
    # Create document context (simulating what classifier provides)
    document_context = {
        'classification': 'government_id',
        'confidence': 0.95,
        'identity_signals': {'pan': True}
    }
    
    # Normalize the document
    normalized_doc = normalizer.normalize_document(pan_ocr, document_context)
    
    # Get original (unmasked) formatted text
    original_text = normalizer.format_normalized_document(normalized_doc, mask=False)
    
    # Get masked formatted text
    masked_text = normalizer.format_normalized_document(normalized_doc, mask=True)
    
    print("\n📄 ORIGINAL (Unmasked):")
    print("-" * 80)
    print(original_text)
    print("-" * 80)
    
    print("\n🔒 MASKED (Purpose-Aware):")
    print("-" * 80)
    print(masked_text)
    print("-" * 80)
    
    # Validation
    print("\n✅ VALIDATION:")
    
    # Check what SHOULD be visible
    checks = {
        "✅ Name visible (RAMESH KUMAR)": "RAMESH KUMAR" in masked_text,
        "✅ PAN Number visible (ABCDE1234F)": "ABCDE1234F" in masked_text,
        "✅ DOB visible (15/08/1990)": "15/08/1990" in masked_text and "[MASKED-DOB]" not in masked_text,
        "✅ Father's name handled": "[MASKED-GUARDIAN-NAME]" in masked_text or "NOT AVAILABLE" in masked_text,
        "✅ Masking metadata present": "MASKING METADATA" in masked_text,
        "✅ Policy is organizational_use": "organizational_use" in masked_text,
    }
    
    for check, passed in checks.items():
        symbol = "✅" if passed else "❌"
        print(f"   {symbol} {check}")
    
    all_passed = all(checks.values())
    if all_passed:
        print("\n🎉 PAN PURPOSE-AWARE MASKING: WORKING PERFECTLY!")
    else:
        print("\n⚠️  Some checks failed!")
    
    return all_passed


def compare_policies():
    """Show side-by-side comparison of what's masked vs visible."""
    
    print("\n\n" + "=" * 80)
    print("MASKING POLICY SUMMARY")
    print("=" * 80)
    
    print("""
AADHAAR CARD:
  ✅ VISIBLE (Organization-Required):
     - Name
     - Aadhaar Number
     - Date of Birth
     - Gender
     - Issuing Authority
  
  🔒 MASKED (Personal Details):
     - Address
     - Guardian Name

PAN CARD:
  ✅ VISIBLE (Organization-Required):
     - Name
     - PAN Number
     - Date of Birth
     - Issuing Authority
  
  🔒 MASKED (Personal Details):
     - Father's Name
     - Signature
""")


if __name__ == "__main__":
    print("\n🔐 PURPOSE-AWARE MASKING TEST SUITE\n")
    print("Testing organizational use policy:")
    print("  • Shows fields required for verification")
    print("  • Masks personal/unnecessary details\n")
    
    # Run tests
    test1_passed = test_aadhaar_masking()
    test2_passed = test_pan_masking()
    
    # Show policy summary
    compare_policies()
    
    # Final result
    print("\n" + "=" * 80)
    if test1_passed and test2_passed:
        print("✅ ✅ ✅  ALL TESTS PASSED - PURPOSE-AWARE MASKING WORKING! ✅ ✅ ✅")
    else:
        print("❌ SOME TESTS FAILED - REVIEW OUTPUT ABOVE")
    print("=" * 80)
