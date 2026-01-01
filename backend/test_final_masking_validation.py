"""
FINAL VALIDATION TEST: Standardized Masking Policy
Tests all document types with exact format requirements
"""

import sys
sys.path.append('d:/Cloud EL/Smart_Cloud_Vault/backend')

from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

def print_header(title):
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80)

def print_section(title):
    print("\n" + title)
    print("-" * 80)

def validate_masking(original, masked, doc_name, visible_fields, masked_fields):
    """Validate that masking rules are correctly applied."""
    print(f"\n✅ VALIDATION: {doc_name}")
    
    all_passed = True
    
    # Check visible fields
    for field in visible_fields:
        if field not in masked:
            print(f"   ❌ FAILED: {field} should be visible but not found")
            all_passed = False
    
    # Check masked fields
    for field_name, marker in masked_fields:
        if marker in masked:
            print(f"   ✅ {field_name}: Properly masked with {marker}")
        else:
            print(f"   ❌ FAILED: {field_name} should show {marker}")
            all_passed = False
    
    # Ensure original != masked
    if original == masked:
        print(f"   ❌ FAILED: Masked copy is identical to original")
        all_passed = False
    else:
        print(f"   ✅ Masked differs from original")
    
    # Check metadata
    if "MASKING METADATA" in masked:
        print(f"   ✅ Masking metadata present")
    else:
        print(f"   ❌ FAILED: Masking metadata missing")
        all_passed = False
    
    return all_passed

def test_aadhaar():
    """Test Aadhaar card masking."""
    print_header("TEST 1: AADHAAR CARD")
    
    ocr = """Government of India
Unique Identification Authority

Name: Akash Kumar
Gender: Male
Date of Birth: 14/08/2001

Address: Mumbai, Maharashtra
Guardian: Rajesh Kumar

1234 5678 9012"""
    
    normalizer = GovernmentDocumentNormalizer()
    context = {'classification': 'government_id', 'confidence': 0.95, 'identity_signals': {'aadhaar': True}}
    
    normalized = normalizer.normalize_document(ocr, context)
    original = normalizer.format_normalized_document(normalized, mask=False)
    masked = normalizer.format_normalized_document(normalized, mask=True)
    
    print_section("ORIGINAL")
    print(original)
    
    print_section("MASKED")
    print(masked)
    
    return validate_masking(
        original, masked, "Aadhaar Card",
        visible_fields=["Akash Kumar", "1234 5678 9012", "Male", "14/08/2001"],
        masked_fields=[("Address", "[MASKED-ADDRESS]"), ("Guardian Name", "[MASKED-GUARDIAN-NAME]")]
    )

def test_pan():
    """Test PAN card masking."""
    print_header("TEST 2: PAN CARD")
    
    ocr = """INCOME TAX DEPARTMENT
Government of India

Permanent Account Number

Name: Akash Kumar
Father's Name: Rajesh Kumar
Date of Birth: 01/06/1995

ABCDE1234F

Signature"""
    
    normalizer = GovernmentDocumentNormalizer()
    context = {'classification': 'government_id', 'confidence': 0.95, 'identity_signals': {'pan': True}}
    
    normalized = normalizer.normalize_document(ocr, context)
    original = normalizer.format_normalized_document(normalized, mask=False)
    masked = normalizer.format_normalized_document(normalized, mask=True)
    
    print_section("ORIGINAL")
    print(original)
    
    print_section("MASKED")
    print(masked)
    
    return validate_masking(
        original, masked, "PAN Card",
        visible_fields=["Akash Kumar", "ABCDE1234F", "01/06/1995"],
        masked_fields=[("Father's Name", "[MASKED-GUARDIAN-NAME]"), ("Signature", "[MASKED-SIGNATURE]")]
    )

def test_driving_license():
    """Test Driving License masking."""
    print_header("TEST 3: DRIVING LICENSE")
    
    ocr = """RTO, Kalahandi

Name: Upendra Kumar Mishra
License Number: DL-KL-123456
Vehicle Class: MCWG
Valid from: 19-01-2008 to 18-01-2028

Date of Birth: 11-03-1988
Blood Group: O+
Father's Name: Dinabandhu Mishra
Address: Sindhekela, Bolangir, Odisha, 767035"""
    
    normalizer = GovernmentDocumentNormalizer()
    context = {'classification': 'government_id', 'confidence': 0.95, 'identity_signals': {'driving_license': True}}
    
    normalized = normalizer.normalize_document(ocr, context)
    original = normalizer.format_normalized_document(normalized, mask=False)
    masked = normalizer.format_normalized_document(normalized, mask=True)
    
    print_section("ORIGINAL")
    print(original)
    
    print_section("MASKED")
    print(masked)
    
    return validate_masking(
        original, masked, "Driving License",
        visible_fields=["Upendra Kumar Mishra", "DL-KL-123456", "MCWG"],
        masked_fields=[
            ("Date of Birth", "[MASKED-DOB]"),
            ("Blood Group", "[MASKED-BLOOD-GROUP]"),
            ("Parent Name", "[MASKED-GUARDIAN-NAME]"),
            ("Address", "[MASKED-ADDRESS]")
        ]
    )

def test_passport():
    """Test Passport masking."""
    print_header("TEST 4: PASSPORT")
    
    ocr = """REPUBLIC OF INDIA
PASSPORT

Name: Akash Kumar
Passport Number: M1234567
Nationality: Indian
Gender: Male
Date of Birth: 14/08/2001
Valid Till: 14/08/2031

Place of Birth: Mumbai
Address: Mumbai, Maharashtra
File Number: ABC123456"""
    
    normalizer = GovernmentDocumentNormalizer()
    context = {'classification': 'government_id', 'confidence': 0.95, 'identity_signals': {'passport': True}}
    
    normalized = normalizer.normalize_document(ocr, context)
    original = normalizer.format_normalized_document(normalized, mask=False, raw_text=ocr)
    masked = normalizer.format_normalized_document(normalized, mask=True, raw_text=ocr)
    
    print_section("ORIGINAL")
    print(original)
    
    print_section("MASKED")
    print(masked)
    
    return validate_masking(
        original, masked, "Passport",
        visible_fields=["Akash Kumar", "M1234567", "Republic of India", "Male", "14/08/2001"],
        masked_fields=[
            ("Place of Birth", "[MASKED]"),
            ("Address", "[MASKED-ADDRESS]"),
            ("File Number", "[MASKED-FILE-NO]")
        ]
    )

def test_voter_id():
    """Test Voter ID masking."""
    print_header("TEST 5: VOTER ID")
    
    ocr = """ELECTION COMMISSION OF INDIA

Name: Akash Kumar
Voter ID: ABC1234567
Gender: Male

Date of Birth: 14/08/2001
Address: Mumbai, Maharashtra
Father's Name: Rajesh Kumar"""
    
    normalizer = GovernmentDocumentNormalizer()
    context = {'classification': 'government_id', 'confidence': 0.95, 'identity_signals': {'voter_id': True}}
    
    normalized = normalizer.normalize_document(ocr, context)
    original = normalizer.format_normalized_document(normalized, mask=False)
    masked = normalizer.format_normalized_document(normalized, mask=True)
    
    print_section("ORIGINAL")
    print(original)
    
    print_section("MASKED")
    print(masked)
    
    return validate_masking(
        original, masked, "Voter ID",
        visible_fields=["Akash Kumar", "ABC1234567", "Male"],
        masked_fields=[
            ("Age", "[MASKED]"),
            ("Address", "[MASKED-ADDRESS]"),
            ("Parent Name", "[MASKED-GUARDIAN-NAME]")
        ]
    )

def test_generic():
    """Test Generic Government ID masking."""
    print_header("TEST 6: GENERIC GOVERNMENT ID")
    
    ocr = """GOVERNMENT AUTHORITY

Identification Document

Name: Akash Kumar
ID Number: XYZ123456789
Valid until: 2030

Address: Mumbai, Maharashtra
Personal information on record"""
    
    normalizer = GovernmentDocumentNormalizer()
    context = {'classification': 'government_id', 'confidence': 0.95, 'identity_signals': {}}
    
    normalized = normalizer.normalize_document(ocr, context)
    original = normalizer.format_normalized_document(normalized, mask=False)
    masked = normalizer.format_normalized_document(normalized, mask=True)
    
    print_section("ORIGINAL")
    print(original)
    
    print_section("MASKED")
    print(masked)
    
    return validate_masking(
        original, masked, "Generic Government ID",
        visible_fields=["Akash Kumar", "XYZ123456789"],
        masked_fields=[("Personal Details", "[MASKED]")]
    )

if __name__ == "__main__":
    print_header("FINAL MASKING POLICY VALIDATION")
    print("""
This test validates the standardized masking policy across all document types.

✔ ALWAYS SHOW: Document Type, Authority, Holder Name, Document ID Number, Validity
❌ ALWAYS MASK: Address, Parent/Guardian Name, Blood Group, Signature, QR Code, Photos

Document-specific rules enforced for: Aadhaar, PAN, DL, Passport, Voter ID, Generic
""")
    
    results = []
    
    try:
        results.append(("Aadhaar Card", test_aadhaar()))
        results.append(("PAN Card", test_pan()))
        results.append(("Driving License", test_driving_license()))
        results.append(("Passport", test_passport()))
        results.append(("Voter ID", test_voter_id()))
        results.append(("Generic ID", test_generic()))
        
        print_header("FINAL RESULTS")
        
        all_passed = True
        for doc_name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{status}: {doc_name}")
            if not passed:
                all_passed = False
        
        print("\n" + "=" * 80)
        if all_passed:
            print("🎉 ALL TESTS PASSED - MASKING POLICY FULLY COMPLIANT 🎉".center(80))
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW OUTPUT ABOVE".center(80))
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
