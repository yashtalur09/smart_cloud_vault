"""Quick validation: Test standardized masking policy is working correctly."""

import sys
sys.path.append('d:/Cloud EL/Smart_Cloud_Vault/backend')

from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

def quick_test():
    print("🔍 QUICK MASKING VALIDATION\n")
    
    # Test 1: Aadhaar
    ocr1 = """Government of India
Name: Test User
DOB: 01/01/2000
Gender: Male
Address: Test Address, Mumbai
1234 5678 9012"""
    
    normalizer = GovernmentDocumentNormalizer()
    context1 = {'classification': 'government_id', 'confidence': 0.95, 'identity_signals': {'aadhaar': True}}
    norm1 = normalizer.normalize_document(ocr1, context1)
    masked1 = normalizer.format_normalized_document(norm1, mask=True)
    
    test1 = all([
        "Test User" in masked1,
        "1234 5678 9012" in masked1,
        "01/01/2000" in masked1,
        ("[MASKED-ADDRESS]" in masked1 or "NOT AVAILABLE" in masked1),  # Address masked or not available
        "MASKING METADATA" in masked1
    ])
    
    # Test 2: PAN
    ocr2 = """INCOME TAX DEPARTMENT
Name: Test User
Father's Name: Test Father
DOB: 01/01/2000
ABCDE1234F"""
    
    context2 = {'classification': 'government_id', 'confidence': 0.95, 'identity_signals': {'pan': True}}
    norm2 = normalizer.normalize_document(ocr2, context2)
    masked2 = normalizer.format_normalized_document(norm2, mask=True)
    
    test2 = all([
        "Test User" in masked2,
        "ABCDE1234F" in masked2,
        "01/01/2000" in masked2,
        ("[MASKED-GUARDIAN-NAME]" in masked2 or "NOT AVAILABLE" in masked2),  # Guardian masked or not available
        ("[MASKED-SIGNATURE]" in masked2 or "NOT AVAILABLE" in masked2),  # Signature masked or not available
        "MASKING METADATA" in masked2
    ])
    
    # Test 3: Driving License
    ocr3 = """RTO Authority
Name: Test User
License Number: DL-XX-123456
DOB: 01/01/2000
Blood Group: O+
Address: Test Address"""
    
    context3 = {'classification': 'government_id', 'confidence': 0.95, 'identity_signals': {'driving_license': True}}
    norm3 = normalizer.normalize_document(ocr3, context3)
    masked3 = normalizer.format_normalized_document(norm3, mask=True)
    
    test3 = all([
        "Test User" in masked3,
        "DL-XX-123456" in masked3,
        "[MASKED-DOB]" in masked3 or "01/01/2000" not in masked3,  # DOB should be masked
        "[MASKED-BLOOD-GROUP]" in masked3,  # Blood group should be masked
        ("[MASKED-ADDRESS]" in masked3 or "NOT AVAILABLE" in masked3),  # Address masked or not available
        "MASKING METADATA" in masked3
    ])
    
    # Results
    print(f"✅ Aadhaar: {'PASS' if test1 else 'FAIL'}")
    print(f"✅ PAN: {'PASS' if test2 else 'FAIL'}")
    print(f"✅ Driving License: {'PASS' if test3 else 'FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 ALL TESTS PASSED - MASKING POLICY OPERATIONAL")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED - REVIEW IMPLEMENTATION")
        return False

if __name__ == "__main__":
    try:
        success = quick_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
