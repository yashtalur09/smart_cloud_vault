# S3 Integration - Developer Quick Reference

## 🔧 Configuration

### Environment Variables

```bash
# .env file
USE_S3_STORAGE=true                           # Enable S3 (false = local)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_ORIGINAL_BUCKET=smartcloud-vault-original
S3_MASKED_BUCKET=smartcloud-vault-masked
```

---

## 📁 Architecture Overview

```
Storage Abstraction Layer
  ├── StorageBackend (Interface)
  │   ├── LocalStorage (Local filesystem)
  │   └── S3Storage (AWS S3)
  └── StorageManager (Facade)
```

---

## 💻 Code Usage

### Import Storage Manager

```python
from storage.storage_factory import storage_manager
```

### Save Files

```python
# Save original file
result = await storage_manager.save_original(
    file_content=file_bytes,
    file_id="abc-123",
    filename="document.pdf",
    company="CompanyA"  # Optional, for S3 organization
)

# Returns:
# {
#     'storage_type': 's3' or 'local',
#     's3_key': 'CompanyA/abc-123/document.pdf',  # If S3
#     'bucket': 'smartcloud-vault-original',      # If S3
#     'path': '/path/to/file',                    # If local
#     'file_id': 'abc-123',
#     'size': 12345
# }

# Save masked file
masked_result = await storage_manager.save_masked(
    file_content=masked_bytes,
    file_id="abc-123",
    filename="document.pdf",
    company="CompanyA"
)
```

### Retrieve Files

```python
# Get original file
file_content = await storage_manager.get_original(
    file_id="abc-123",
    storage_key="CompanyA/abc-123/document.pdf"  # Required for S3
)

# Get masked file
masked_content = await storage_manager.get_masked(
    file_id="abc-123",
    storage_key="CompanyA/abc-123/document_masked.pdf"
)

# Returns bytes or None if not found
```

### Delete Files

```python
# Delete original
success = await storage_manager.delete_original(
    file_id="abc-123",
    storage_key="CompanyA/abc-123/document.pdf"
)

# Delete masked
success = await storage_manager.delete_masked(
    file_id="abc-123",
    storage_key="CompanyA/abc-123/document_masked.pdf"
)
```

---

## 🗄️ MongoDB Schema

### File Metadata Fields

```javascript
{
  // Existing fields
  "file_id": "abc-123-uuid",
  "original_filename": "document.pdf",
  "company": "CompanyA",
  "uploader_email": "user@example.com",
  
  // NEW: Storage backend fields
  "storage_type": "s3",  // or "local"
  "original_s3_key": "CompanyA/abc-123/document.pdf",
  "masked_s3_key": "CompanyA/abc-123/document_masked.pdf",
  "original_bucket": "smartcloud-vault-original",
  "masked_bucket": "smartcloud-vault-masked",
  "masked_file_path": "CompanyA/abc-123/document_masked.pdf"  // Path or S3 key
}
```

---

## 🔄 Storage Flow

### Upload Flow

```python
# 1. Upload file
storage_result = await storage_manager.save_original(
    file_content, file_id, filename, company
)

# 2. Store metadata in MongoDB
metadata = {
    "file_id": file_id,
    "storage_type": storage_result['storage_type'],
    "original_s3_key": storage_result.get('s3_key'),
    "original_bucket": storage_result.get('bucket'),
    # ... other fields
}
await db.files.insert_one(metadata)

# 3. Process and mask file
masked_content = await process_and_mask(file_content)

# 4. Save masked version
masked_result = await storage_manager.save_masked(
    masked_content, file_id, filename, company
)

# 5. Update metadata
await db.files.update_one(
    {"file_id": file_id},
    {"$set": {
        "masked_s3_key": masked_result.get('s3_key'),
        "masked_bucket": masked_result.get('bucket')
    }}
)
```

### Download Flow

```python
# 1. Get file metadata from MongoDB
file_doc = await db.files.find_one({"file_id": file_id})

# 2. Check email match
if requester_email == file_doc['uploader_email']:
    # Return original
    storage_key = file_doc.get('original_s3_key')
    content = await storage_manager.get_original(file_id, storage_key)
else:
    # Return masked
    storage_key = file_doc.get('masked_s3_key')
    content = await storage_manager.get_masked(file_id, storage_key)

# 3. Return file to user
return StreamingResponse(BytesIO(content), ...)
```

---

## 🧪 Testing

### Test S3 Connection

```python
from storage.s3_storage import S3Storage
from config import settings

s3 = S3Storage(
    original_bucket=settings.s3_original_bucket,
    masked_bucket=settings.s3_masked_bucket
)

# Test upload
test_content = b"Hello, S3!"
result = await s3.save_original(
    test_content,
    "test-123",
    "test.txt",
    "TestCompany"
)
print(result)

# Test download
content = await s3.get_original("test-123", result['s3_key'])
print(content.decode())

# Test delete
success = await s3.delete_original("test-123", result['s3_key'])
```

### Test with Local Storage

```python
# Set in .env:
# USE_S3_STORAGE=false

from storage.storage_factory import storage_manager

# All operations work the same!
result = await storage_manager.save_original(
    b"Test content",
    "test-456",
    "test.txt"
)
```

---

## 🐛 Debugging

### Check Which Storage Backend

```python
from storage.storage_factory import storage_manager

# Check backend type
print(type(storage_manager.backend).__name__)
# Output: "S3Storage" or "LocalStorage"
```

### View Logs

```python
import logging
logging.basicConfig(level=logging.INFO)

# You'll see:
# INFO: Initializing S3 storage backend...
# INFO: S3 client initialized for region: us-east-1
```

### Common Issues

**Issue**: Files saved but can't retrieve

**Solution**: Make sure you're passing the `storage_key` when fetching S3 files:

```python
# ❌ Wrong (S3 needs key)
content = await storage_manager.get_original(file_id)

# ✅ Correct
storage_key = file_doc.get('original_s3_key')
content = await storage_manager.get_original(file_id, storage_key)
```

---

## 🔐 Security Notes

### Never Log Credentials

```python
# ❌ Don't do this
logger.info(f"Using AWS key: {settings.aws_access_key_id}")

# ✅ Do this
logger.info("S3 storage initialized")
```

### Pre-signed URLs (Optional)

For temporary public access:

```python
from storage.s3_storage import S3Storage

s3 = S3Storage(...)
url = s3.generate_presigned_url(
    bucket="smartcloud-vault-original",
    s3_key="CompanyA/abc-123/document.pdf",
    expiration=3600  # 1 hour
)

# Returns: https://smartcloud-vault-original.s3.amazonaws.com/...?signature=...
```

---

## 📊 S3 Key Format

```
{company}/{file_id}/{filename}
```

**Examples:**
- Original: `CompanyA/abc-123/invoice.pdf`
- Masked: `CompanyA/abc-123/invoice_masked.pdf`
- OCR Text: `CompanyA/abc-123/image.txt` (original image replaced with text)

**Without company:**
```
files/{file_id}/{filename}
```

---

## ♻️ Backward Compatibility

The system is fully backward compatible:

1. **Old files** (local storage):
   - `storage_type`: `null` or `"local"`
   - `original_s3_key`: `null`
   - Still accessible via `storage_manager.get_original(file_id)`

2. **New files** (S3 storage):
   - `storage_type`: `"s3"`
   - `original_s3_key`: `"CompanyA/abc-123/file.pdf"`
   - Requires `storage_key` parameter

---

## 🚀 Performance Tips

### Batch Operations

For multiple files, use asyncio.gather:

```python
import asyncio

files_to_download = [
    (file_id_1, s3_key_1),
    (file_id_2, s3_key_2),
    (file_id_3, s3_key_3)
]

contents = await asyncio.gather(*[
    storage_manager.get_original(fid, key)
    for fid, key in files_to_download
])
```

### Caching

Consider caching frequently accessed files:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_cached_file(file_id, storage_key):
    return await storage_manager.get_original(file_id, storage_key)
```

---

## 📝 Migration Checklist

When migrating code to use storage manager:

- [ ] Replace `file_storage.save_file()` → `storage_manager.save_original()`
- [ ] Replace `file_storage.get_file()` → `storage_manager.get_original(file_id, s3_key)`
- [ ] Replace `file_storage.save_masked_file()` → `storage_manager.save_masked()`
- [ ] Replace `file_storage.get_masked_file()` → `storage_manager.get_masked(file_id, s3_key)`
- [ ] Update MongoDB schema to include storage fields
- [ ] Pass `storage_key` when retrieving S3 files
- [ ] Handle both `storage_type='local'` and `storage_type='s3'`

---

## 🔗 Related Files

- `backend/storage/storage_interface.py` - Abstract base class
- `backend/storage/s3_storage.py` - S3 implementation
- `backend/storage/local_storage.py` - Local storage wrapper
- `backend/storage/storage_factory.py` - Factory and initialization
- `backend/api/upload.py` - Upload endpoint (uses storage manager)
- `backend/api/download.py` - Download endpoint (uses storage manager)
- `backend/models/schemas.py` - MongoDB schema with S3 fields

---

**Quick Start:**

```bash
# 1. Install boto3
pip install boto3

# 2. Configure .env
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1

# 3. Create S3 buckets
aws s3 mb s3://smartcloud-vault-original
aws s3 mb s3://smartcloud-vault-masked

# 4. Start app
python main.py
```

Done! 🎉
