"""Test purpose-aware masking with actual sensitive data."""

import sys
sys.path.append('d:/Cloud EL/Smart_Cloud_Vault/backend')

from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

def test_aadhaar_with_address():
    """Test Aadhaar with actual address to verify masking."""
    
    print("=" * 80)
    print("TEST: AADHAAR WITH ADDRESS - PURPOSE-AWARE MASKING")
    print("=" * 80)
    
    # Aadhaar OCR with address
    aadhaar_ocr = """Government of India
    
Name: Harsh Yadav
DOB: 06.09.1984
Gender: Male

8108 6494 9408 6584

Address:
House No 123, Street Name
Sector 45, Noida
Uttar Pradesh - 201301"""
    
    normalizer = GovernmentDocumentNormalizer()
    
    document_context = {
        'classification': 'government_id',
        'confidence': 0.95,
        'identity_signals': {'aadhaar': True}
    }
    
    normalized_doc = normalizer.normalize_document(aadhaar_ocr, document_context)
    
    original_text = normalizer.format_normalized_document(normalized_doc, mask=False)
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
    
    checks = {
        "✅ Name visible": "Harsh Yadav" in masked_text,
        "✅ Aadhaar visible": "8108 6494 9408 6584" in masked_text,
        "✅ DOB visible": "06.09.1984" in masked_text,
        "✅ Gender visible": "Male" in masked_text,
        "❌ Address MASKED": "[MASKED-ADDRESS]" in masked_text and "House No 123" not in masked_text and "Noida" not in masked_text,
        "✅ Metadata present": "MASKING METADATA" in masked_text,
    }
    
    for check, passed in checks.items():
        symbol = "✅" if passed else "❌"
        print(f"   {symbol} {check}")
    
    all_passed = all(checks.values())
    
    # Compare original vs masked
    print("\n📊 COMPARISON:")
    print(f"   Original contains address: {'House No 123' in original_text}")
    print(f"   Masked hides address: {'[MASKED-ADDRESS]' in masked_text}")
    print(f"   Masked shows required fields: {all([x in masked_text for x in ['Harsh Yadav', '8108 6494 9408 6584', '06.09.1984', 'Male']])}")
    
    if all_passed:
        print("\n🎉 ADDRESS MASKING WORKING PERFECTLY!")
    else:
        print("\n⚠️  Some checks failed!")
    
    return all_passed


def test_pan_with_father_name():
    """Test PAN with actual father name to verify masking."""
    
    print("\n\n" + "=" * 80)
    print("TEST: PAN WITH FATHER'S NAME - PURPOSE-AWARE MASKING")
    print("=" * 80)
    
    pan_ocr = """INCOME TAX DEPARTMENT
GOVT. OF INDIA

Permanent Account Number Card

Name: AMIT SHARMA
Father's Name: RAJESH SHARMA
Date of Birth: 25/03/1985

BXPPS1234K

Signature"""
    
    normalizer = GovernmentDocumentNormalizer()
    
    document_context = {
        'classification': 'government_id',
        'confidence': 0.95,
        'identity_signals': {'pan': True}
    }
    
    normalized_doc = normalizer.normalize_document(pan_ocr, document_context)
    
    original_text = normalizer.format_normalized_document(normalized_doc, mask=False)
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
    
    checks = {
        "✅ Name visible": "AMIT SHARMA" in masked_text,
        "✅ PAN visible": "BXPPS1234K" in masked_text,
        "✅ DOB visible": "25/03/1985" in masked_text,
        "❌ Father's name MASKED": "[MASKED-GUARDIAN-NAME]" in masked_text and "RAJESH SHARMA" not in masked_text,
        "✅ Metadata present": "MASKING METADATA" in masked_text,
    }
    
    for check, passed in checks.items():
        symbol = "✅" if passed else "❌"
        print(f"   {symbol} {check}")
    
    all_passed = all(checks.values())
    
    # Compare original vs masked
    print("\n📊 COMPARISON:")
    print(f"   Original contains father's name: {'RAJESH SHARMA' in original_text}")
    print(f"   Masked hides father's name: {'[MASKED-GUARDIAN-NAME]' in masked_text}")
    print(f"   Masked shows required fields: {all([x in masked_text for x in ['AMIT SHARMA', 'BXPPS1234K', '25/03/1985']])}")
    
    if all_passed:
        print("\n🎉 FATHER'S NAME MASKING WORKING PERFECTLY!")
    else:
        print("\n⚠️  Some checks failed!")
    
    return all_passed


if __name__ == "__main__":
    print("\n🔐 PURPOSE-AWARE MASKING - SENSITIVE DATA TEST\n")
    print("Testing that personal data is properly masked while")
    print("organization-required fields remain visible.\n")
    
    test1 = test_aadhaar_with_address()
    test2 = test_pan_with_father_name()
    
    print("\n" + "=" * 80)
    if test1 and test2:
        print("✅ ✅ ✅  ALL SENSITIVE DATA PROPERLY MASKED! ✅ ✅ ✅")
    else:
        print("❌ SOME TESTS FAILED - REVIEW OUTPUT ABOVE")
    print("=" * 80)
