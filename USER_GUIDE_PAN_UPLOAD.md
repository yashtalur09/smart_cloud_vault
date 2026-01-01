# What to Expect When You Upload a PAN Card

## Step-by-Step Guide

### 1. Upload Your PAN Card Image

When you upload your PAN card through the frontend:
- System will automatically detect it's a government ID
- OCR will extract text with improved preprocessing
- Document will be normalized into standard format
- Two versions will be created: **Unmasked** and **Masked**

---

### 2. What You'll See in the Unmasked File

**File Location:** `storage/files/{file_id}.txt`

**Purpose:** Internal records, compliance, audit trail

**Content Example:**
```
DOCUMENT TYPE: PAN Card
Authority: Income Tax Department, Government of India

Name: TALUR YASHWANTH
PAN Number: BQUPY0939B
Date of Birth: 09/01/2006

Father's Name: TALUR NATASHEKAR
Signature Reference: Present

---
Field Confidence (Low):
- date_of_birth: 75%
```

**What's Included:**
- ✅ All personal information (full name, DOB, father's name)
- ✅ Government ID number (PAN)
- ✅ Document metadata (authority, type)
- ✅ Quality indicators (confidence scores for low-confidence fields)

**Use Cases:**
- Internal compliance team review
- Audit trails
- Legal requirements
- Original record keeping

---

### 3. What You'll See in the Masked File

**File Location:** `storage/masked/{file_id}_masked.txt`

**Purpose:** External sharing, organizational use, reduced liability

**Content Example:**
```
DOCUMENT TYPE: PAN Card
Authority: Income Tax Department, Government of India

Name: TALUR YASHWANTH
PAN Number: BQUPY0939B
Date of Birth: [MASKED-DOB]

Father's Name: [MASKED-FATHER-NAME]
Signature Reference: [MASKED-SIGNATURE]

---
MASKING METADATA:
Policy: organizational_use
Document Type: PAN Card
Visible Fields: Name, PAN Number
Masked Fields: Date of Birth, Father's Name, Signature Reference
```

**What's Included:**
- ✅ Name (needed for identification)
- ✅ PAN Number (needed for reference)
- ❌ DOB (replaced with `[MASKED-DOB]`)
- ❌ Father's Name (replaced with `[MASKED-FATHER-NAME]`)
- ❌ Signature (replaced with `[MASKED-SIGNATURE]`)

**Plus Metadata:**
- Policy applied (organizational_use)
- List of visible fields
- List of masked fields

**Use Cases:**
- Sharing with external parties
- HR/payroll processing
- Reduced PII exposure
- Compliance with data minimization

---

## Field-by-Field Breakdown

### Always Visible (Both Files)

| Field | Why Visible? |
|-------|--------------|
| Name | Needed for identification |
| PAN Number | Primary identifier, needed for verification |
| Document Type | Metadata for processing |
| Authority | Verification of authenticity |

### Hidden in Masked File Only

| Field | Why Masked? | Token Used |
|-------|-------------|------------|
| Date of Birth | Sensitive PII, identity theft risk | `[MASKED-DOB]` |
| Father's Name | Personal family information | `[MASKED-FATHER-NAME]` |
| Signature | Forgery prevention | `[MASKED-SIGNATURE]` |
| Address | Privacy protection | `[MASKED-ADDRESS]` |

---

## Confidence Scores Explained

The system shows confidence scores for fields that may have lower accuracy:

```
Field Confidence (Low):
- date_of_birth: 75%
- gender: 0%
```

**What This Means:**

- **75%**: System is fairly confident but recommend manual verification
- **0%**: Field not found/extracted (shows as "NOT AVAILABLE" in output)
- **85%+**: High confidence, usually accurate (not shown in low confidence list)

**When to Verify Manually:**
- Any field with confidence < 80%
- Fields showing "NOT AVAILABLE"
- If OCR input was very poor quality

---

## Quality Indicators

### Good Quality Upload ✅

**Indicators:**
- Overall confidence: **60%+**
- Most fields extracted: **4-5 out of 5**
- Clean formatting in output
- No major OCR artifacts

**Example:**
```
Name: TALUR YASHWANTH (95%)
PAN: BQUPY0939B (98%)
DOB: 09/01/2006 (75%)
Father: TALUR NATASHEKAR (92%)
```

### Poor Quality Upload ⚠️

**Indicators:**
- Overall confidence: **<50%**
- Many fields missing: **<3 out of 5**
- "NOT AVAILABLE" for multiple fields
- Strange characters or artifacts

**Example:**
```
Name: NOT AVAILABLE (0%)
PAN: BQUPY0939B (98%)
DOB: NOT AVAILABLE (0%)
Father: NOT AVAILABLE (0%)
```

**What to Do:**
1. Try uploading a clearer image
2. Ensure good lighting and no glare
3. Take photo straight-on (not at angle)
4. Higher resolution is better (1000px+ width)

---

## Common Questions

### Q: Why is the name different from what I typed?
**A:** The system extracts the name from the image using OCR. It reads what's printed on the card, not what you type.

### Q: Why is "Date of Birth" masked but "PAN Number" visible?
**A:** PAN number is the primary identifier needed for verification. DOB is more sensitive PII that's not strictly needed for most organizational use cases.

### Q: Can I control what gets masked?
**A:** Yes! The masking policy is configurable. Current policy is `organizational_use`. Other policies (e.g., `full_mask`, `audit_only`) can mask more or less.

### Q: What if extraction is wrong?
**A:** Check the confidence scores. If a field has low confidence (<80%), you should manually verify it. The system shows these in the "Field Confidence (Low)" section.

### Q: Do both files get stored permanently?
**A:** Yes, both versions are stored:
- Original/Unmasked: `storage/files/`
- Masked: `storage/masked/`
- Image is deleted after OCR (only text is kept)

### Q: Is the masked version secure for email?
**A:** Yes! The masked version is safe to share via email or with external parties. Sensitive PII is replaced with tokens, reducing liability.

---

## File Naming Convention

- **Unmasked:** `{file_id}.txt`
- **Masked:** `{file_id}_masked.txt`

Where `{file_id}` is a unique identifier like: `abc123def456`

---

## Troubleshooting

### Problem: Names are garbled or wrong

**Solution:**
1. Ensure good image quality (clear, well-lit, straight-on)
2. Check if image resolution is at least 1000px wide
3. Avoid shadows, glare, or fold marks
4. Re-upload with better quality image

### Problem: Date of Birth shows "NOT AVAILABLE"

**Possible Causes:**
- DOB text is too small or blurry
- DOB is in unusual format
- OCR couldn't read the numbers

**Solution:**
- Zoom in closer when taking photo
- Ensure numbers are clearly visible
- Try a different scan/photo

### Problem: Both files look the same

**This is now fixed!** But if you still see this:
1. Clear your browser cache
2. Re-upload the file
3. Check that you're comparing the right files:
   - Unmasked: `{file_id}.txt`
   - Masked: `{file_id}_masked.txt`

---

## Summary

**Unmasked File:**
- 📄 Full data for internal use
- 🔒 Store securely
- ✅ Use for compliance/audit

**Masked File:**
- 📄 Reduced data for external sharing
- 📧 Safe to email
- ✅ Use for organizational workflows

**Both files are automatically generated on upload!**

---

*Last updated: December 27, 2025*
