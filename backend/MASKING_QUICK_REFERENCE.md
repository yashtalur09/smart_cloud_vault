# Purpose-Aware Masking - Quick Reference

## What Is It?

A privacy-preserving masking system that shows **only what organizations need** while protecting employee personal information.

## Key Principle

**"Show only what's needed for verification, mask everything else"**

## Quick Comparison

| Field | Aadhaar | PAN | Reason |
|-------|---------|-----|--------|
| Name | ✅ Visible | ✅ Visible | Identity verification |
| Document ID | ✅ Visible | ✅ Visible | Document verification |
| DOB | ✅ Visible | ✅ Visible | Age verification |
| Gender | ✅ Visible | N/A | Identity verification |
| Authority | ✅ Visible | ✅ Visible | Authenticity verification |
| Address | 🔒 Masked | 🔒 Masked | Personal detail - not needed |
| Guardian Name | 🔒 Masked | 🔒 Masked | Personal detail - not needed |

## How to Use

```python
from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

normalizer = GovernmentDocumentNormalizer()

# Step 1: Normalize document
normalized_doc = normalizer.normalize_document(raw_ocr, document_context)

# Step 2: Get unmasked version (full record)
original = normalizer.format_normalized_document(normalized_doc, mask=False)

# Step 3: Get masked version (organization use)
masked = normalizer.format_normalized_document(normalized_doc, mask=True)
```

## What's Included in Masked Version?

Every masked document includes:

1. **Structured Document Data**: Clean template format
2. **Organization-Required Fields**: Name, ID, DOB, etc. (visible)
3. **Masked Personal Details**: Address, Guardian Name (masked)
4. **Masking Metadata**:
   - Policy type: `organizational_use`
   - Document type: Aadhaar, PAN, etc.
   - List of visible fields
   - List of masked fields

## Example Output

### Aadhaar Card - Masked Version

```
DOCUMENT TYPE: Aadhaar Card

Name:
PRIYA SHARMA

Aadhaar Number:
2345 6789 0123 4567

Date of Birth:
15.06.1992

Gender:
Female

Address:
[MASKED-ADDRESS]

Issuing Authority:
Unique Identification Authority of India (UIDAI)

---
MASKING METADATA:
Policy: organizational_use
Document Type: Aadhaar Card
Visible Fields: Name, Aadhaar Number, Date of Birth, Gender, Issuing Authority
Masked Fields: Address, Guardian Name
```

### PAN Card - Masked Version

```
DOCUMENT TYPE: PAN Card

Name:
VIKRAM SINGH

PAN Number:
CDFPS9876Q

Father's Name:
[MASKED-GUARDIAN-NAME]

Date of Birth:
20/11/1988

Issuing Authority:
INCOME TAX DEPARTMENT

---
MASKING METADATA:
Policy: organizational_use
Document Type: PAN Card
Visible Fields: Name, PAN Number, Date of Birth, Issuing Authority
Masked Fields: Father's Name, Signature
```

## Files Modified

- `backend/ai_engine/govt_doc_normalizer.py` - Masking logic only

## Files NOT Modified

- OCR processing
- Document classification
- Field extraction
- Database storage
- API endpoints
- Access control

## Testing

Run comprehensive tests:

```bash
# Test purpose-aware masking
python test_purpose_aware_masking.py

# Test with sensitive data
python test_sensitive_masking.py

# Complete end-to-end workflow
python test_complete_workflow.py
```

All tests should show: `✅ ALL TESTS PASSED`

## Benefits

### For Organizations
- ✅ Verify employee identity
- ✅ Validate documents
- ✅ Check eligibility
- ✅ Reduced liability

### For Employees
- ✅ Address privacy
- ✅ Guardian name privacy
- ✅ Minimal data exposure
- ✅ Compliance with privacy laws

## Supported Documents

1. ✅ Aadhaar Card (12 or 16-digit)
2. ✅ PAN Card
3. ✅ Passport (template ready)
4. ✅ Driving License (template ready)
5. ✅ Voter ID (template ready)
6. ✅ Generic Government ID (fallback)

## Questions?

See `PURPOSE_AWARE_MASKING_SUMMARY.md` for detailed documentation.
