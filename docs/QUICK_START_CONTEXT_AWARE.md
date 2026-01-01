# Quick Start Guide - Context-Aware Intelligence Engine

## 🚀 Getting Started in 5 Minutes

### Step 1: Test the Engine

Run the test script to see the new capabilities:

```bash
cd backend
python test_context_aware_engine.py
```

This will demonstrate:
- ✅ Invoice processing with automatic field detection
- ✅ Receipt processing
- ✅ HR document processing
- ✅ Bank statement processing
- ✅ Old vs New comparison
- ✅ Explainability features

### Step 2: Try Sample Documents

Upload sample files through the API:

```bash
# Invoice
curl -X POST http://localhost:8000/api/upload \
  -F "file=@docs/sample_files/sample_invoice.txt" \
  -F "company=TestCorp" \
  -F "department=Finance" \
  -F "uploader_email=test@example.com"
```

Response includes:
- `document_type` - Automatically detected as "invoice"
- `document_type_confidence` - Classification confidence
- `semantic_fields_count` - Number of detected fields
- `masking_explanations` - Why each field was masked

### Step 3: View Results

Get the context-aware analysis:

```bash
# Replace {file_id} with the ID from upload response
curl http://localhost:8000/api/upload/files/{file_id}/context-analysis
```

Get masking explanations:

```bash
curl http://localhost:8000/api/upload/files/{file_id}/masking-explanation
```

### Step 4: Download Masked File

```bash
curl http://localhost:8000/api/download/masked/{file_id} \
  -H "X-Requester-Email: test@example.com" \
  -o masked_output.txt
```

## 🎯 Key Differences from Old System

### OLD: Keyword-Based (Limited)
```
❌ Looks for specific keywords like "SSN", "credit card"
❌ Fails on implicit fields (invoice numbers, PO numbers)
❌ No document understanding
❌ Fixed rules only
❌ No explanations
```

### NEW: Context-Aware (Intelligent)
```
✅ Understands document type (invoice, HR, financial)
✅ Detects fields by semantic meaning
✅ Automatically finds invoice numbers, PO numbers, etc.
✅ Adjusts masking based on context
✅ Explains every decision
✅ Works on unseen document formats
```

## 📋 Example Output

### Invoice Processing

**Input:**
```
INVOICE
Invoice Number: INV-2024-8734
Purchase Order: PO-456789
Bill To: ABC Corporation
Total Amount: $18,356.08
```

**Output:**
```
INVOICE
Invoice Number: [MASKED-INVOICE-ID]
Purchase Order: [MASKED-PO]
Bill To: [MASKED-ORG]
Total Amount: [MASKED-AMOUNT]
```

**Explanation:**
```json
[
  {
    "field": "invoice_number",
    "reason": "Unique financial transaction identifier",
    "sensitivity": "high",
    "confidence": 0.92
  },
  {
    "field": "po_number",
    "reason": "Business confidential procurement reference",
    "sensitivity": "high",
    "confidence": 0.90
  }
]
```

## 🔍 Understanding Results

### Document Context
```json
{
  "type": "invoice",
  "confidence": 0.85,
  "keywords": ["invoice", "bill to", "total amount"],
  "reasoning": "Identified as invoice based on 12 matching keywords"
}
```

### Detected Fields
```json
{
  "name": "invoice_number",
  "value_preview": "INV-2024-8734",
  "sensitivity": "high",
  "confidence": 0.92,
  "reason": "Unique financial transaction identifier"
}
```

### Masking Explanation
```json
{
  "field": "invoice_number",
  "original_value": "INV-2024-8734",
  "masked_value": "[MASKED-INVOICE-ID]",
  "reason": "Unique financial transaction identifier",
  "sensitivity": "high",
  "confidence": 0.92
}
```

## 📊 Sensitivity Levels

| Level | Examples | Auto-Mask? |
|-------|----------|------------|
| **CRITICAL** | SSN, DOB, Account Numbers | ✅ Always |
| **HIGH** | Invoice ID, Employee ID, Addresses | ✅ Yes |
| **MEDIUM** | Amounts, Customer IDs | ⚠️ Configurable |
| **LOW** | Product Names, Quantities | ❌ No |

## 🎨 Customization Options

### Adjust Sensitivity Threshold

```python
result = context_engine.process_document(
    text=document_text,
    apply_masking=True,
    min_sensitivity=SensitivityLevel.HIGH  # Only mask HIGH and CRITICAL
)
```

### Preserve or Compact Layout

```python
result = context_engine.process_document(
    text=document_text,
    apply_masking=True,
    preserve_structure=True  # Keep original formatting
)
```

### Get Analysis Without Masking

```python
result = context_engine.process_document(
    text=document_text,
    apply_masking=False  # Just analyze, don't mask
)
```

## 🧪 Testing Your Own Documents

### 1. Prepare Document
Create a `.txt` file with your document content

### 2. Upload via API
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@your_document.txt" \
  -F "company=YourCompany" \
  -F "department=YourDept" \
  -F "uploader_email=your@email.com"
```

### 3. Check Results
```bash
# Get analysis
curl http://localhost:8000/api/upload/files/{file_id}/context-analysis

# Get explanations
curl http://localhost:8000/api/upload/files/{file_id}/masking-explanation
```

### 4. Download Masked Version
```bash
curl http://localhost:8000/api/download/masked/{file_id} \
  -H "X-Requester-Email: your@email.com" \
  -o masked_output.txt
```

## 🔧 Troubleshooting

### Issue: Document Type Not Detected Correctly
**Solution:** Check that your document includes clear indicators (keywords, patterns)

### Issue: Important Fields Not Masked
**Solution:** Lower the `min_sensitivity` threshold or check field formatting

### Issue: Too Many Fields Masked
**Solution:** Increase the `min_sensitivity` threshold

### Issue: Low Confidence Scores
**Solution:** Improve document structure and clarity

## 📖 Next Steps

1. ✅ Run test script: `python test_context_aware_engine.py`
2. ✅ Try sample documents
3. ✅ Test with your own documents
4. ✅ Review explanations
5. ✅ Adjust sensitivity thresholds
6. ✅ Integrate with your workflow

## 🌟 Key Benefits

### For Security Teams
- 🔒 Automatic detection of sensitive fields
- 📊 Confidence scores for audit trails
- 🎯 Context-aware protection

### For Compliance Officers
- 📝 Complete transparency
- ✅ Audit-ready explanations
- 📈 Configurable policies

### For Users
- ⚡ Fast processing
- 🎨 Preserved formatting
- 🔍 Clear reasoning

### For Developers
- 🛠️ Easy integration
- 📡 RESTful API
- 🐍 Python SDK

## 💡 Pro Tips

1. **Use Clear Headers:** Documents with clear section headers are classified more accurately

2. **Consistent Formatting:** Standard formats improve field detection

3. **Review Explanations:** Check masking explanations to understand system behavior

4. **Adjust Thresholds:** Start with default settings, then customize based on your needs

5. **Test Samples First:** Always test with sample data before production use

## 🎓 Learn More

- 📚 Full Documentation: `docs/CONTEXT_AWARE_ENGINE.md`
- 🔬 Test Script: `backend/test_context_aware_engine.py`
- 📁 Sample Files: `docs/sample_files/`
- 🌐 API Docs: http://localhost:8000/docs

## ✅ Success Checklist

- [ ] Ran test script successfully
- [ ] Tested with sample invoice
- [ ] Viewed context analysis results
- [ ] Reviewed masking explanations
- [ ] Downloaded masked file
- [ ] Understood sensitivity levels
- [ ] Tested with own document
- [ ] Ready for production use!

---

**Need Help?** Check the troubleshooting section or review the full documentation.

**Want to Contribute?** The engine is extensible - add your own document types and field patterns!
