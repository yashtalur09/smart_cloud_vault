# AWS S3 Integration - Complete Setup Guide

## 📋 Overview

SmartCloud Vault now supports AWS S3 for document storage with a **dual-bucket architecture**:

- **Bucket 1**: `smartcloud-vault-original` - Original (unmasked) documents
- **Bucket 2**: `smartcloud-vault-masked` - Masked/encrypted documents

This provides:
- ✅ Scalable cloud storage
- ✅ High availability and durability
- ✅ Encryption at rest (AES-256)
- ✅ Organized file structure by company
- ✅ Easy migration from local to cloud storage

---

## 🏗️ Architecture

### Storage Flow

```
┌─────────────────────┐
│   File Upload       │
│  (via Frontend)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Backend API (FastAPI)                  │
│  • Validates file                       │
│  • Generates file_id                    │
│  • Stores metadata in MongoDB           │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Storage Manager (Abstraction Layer)    │
│  • Delegates to configured backend      │
│  • Local Storage OR S3 Storage          │
└──────────┬──────────────────────────────┘
           │
           ├─── Local Storage ────► ./storage/uploads/
           │                        ./storage/masked/
           │
           └─── S3 Storage ────┐
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
    ┌───────────────────────┐   ┌────────────────────────┐
    │  Original Bucket      │   │  Masked Bucket         │
    │  smartcloud-vault-    │   │  smartcloud-vault-     │
    │  original             │   │  masked                │
    │                       │   │                        │
    │  company/file_id/     │   │  company/file_id/      │
    │    document.pdf       │   │    document_masked.pdf │
    └───────────────────────┘   └────────────────────────┘
```

### Access Control Flow

```
User Requests File
       │
       ▼
Backend checks email
       │
       ├─── Email matches uploader ────► Fetch from ORIGINAL bucket
       │
       └─── Email does NOT match ─────► Fetch from MASKED bucket
```

---

## ⚙️ Prerequisites

1. **AWS Account** - [Sign up here](https://aws.amazon.com/)
2. **AWS CLI** (optional but recommended) - [Install guide](https://aws.amazon.com/cli/)
3. **IAM User** with S3 permissions

---

## 🔧 Step 1: AWS Setup

### 1.1 Create IAM User

1. Go to AWS Console → **IAM** → **Users** → **Add users**
2. User name: `smartcloud-vault-s3-user`
3. Select: **Programmatic access** (Access key - API, CLI)
4. Click **Next: Permissions**

### 1.2 Attach S3 Policy

Create a custom policy with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::smartcloud-vault-original/*",
        "arn:aws:s3:::smartcloud-vault-masked/*",
        "arn:aws:s3:::smartcloud-vault-original",
        "arn:aws:s3:::smartcloud-vault-masked"
      ]
    }
  ]
}
```

**Steps:**
1. IAM → **Policies** → **Create policy**
2. Choose **JSON** tab
3. Paste the policy above
4. Name: `SmartCloudVault-S3-Policy`
5. **Create policy**
6. Attach to your IAM user

### 1.3 Get AWS Credentials

After creating the user:
1. Save the **Access Key ID** and **Secret Access Key**
2. ⚠️ **IMPORTANT**: You'll only see the secret key once - save it securely!

---

## 🪣 Step 2: Create S3 Buckets

### Option A: AWS Console (GUI)

1. Go to **S3** → **Create bucket**

2. **Bucket 1: Original Documents**
   - Name: `smartcloud-vault-original`
   - Region: Choose your preferred region (e.g., `us-east-1`)
   - Block all public access: ✅ **ENABLED** (critical for security)
   - Bucket Versioning: Optional (recommended)
   - Encryption: Enable **Server-side encryption with Amazon S3 managed keys (SSE-S3)**
   - Click **Create bucket**

3. **Bucket 2: Masked Documents**
   - Name: `smartcloud-vault-masked`
   - Same settings as above
   - Click **Create bucket**

### Option B: AWS CLI (Command Line)

```bash
# Set your region
export AWS_REGION="us-east-1"

# Create original bucket
aws s3 mb s3://smartcloud-vault-original --region $AWS_REGION

# Create masked bucket
aws s3 mb s3://smartcloud-vault-masked --region $AWS_REGION

# Block public access (CRITICAL)
aws s3api put-public-access-block \
    --bucket smartcloud-vault-original \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

aws s3api put-public-access-block \
    --bucket smartcloud-vault-masked \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket smartcloud-vault-original \
    --server-side-encryption-configuration \
    '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'

aws s3api put-bucket-encryption \
    --bucket smartcloud-vault-masked \
    --server-side-encryption-configuration \
    '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
```

---

## 📝 Step 3: Backend Configuration

### 3.1 Create/Update `.env` File

Create a `.env` file in the `backend/` directory:

```bash
# MongoDB (existing)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=smartcloud_vault

# JWT (existing)
SECRET_KEY=your-secret-key-change-this-in-production

# Storage Configuration
USE_S3_STORAGE=true                           # Set to 'false' to use local storage

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE        # Your AWS access key
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY  # Your AWS secret key
AWS_REGION=us-east-1                          # Your bucket region
S3_ORIGINAL_BUCKET=smartcloud-vault-original  # Original documents bucket
S3_MASKED_BUCKET=smartcloud-vault-masked      # Masked documents bucket

# CORS (existing)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**⚠️ Security Notes:**
- Never commit `.env` to version control
- Add `.env` to `.gitignore`
- Use different credentials for production
- Rotate keys regularly

### 3.2 Install Dependencies

```bash
cd backend
pip install boto3 botocore
# Or install all requirements:
pip install -r requirements.txt
```

---

## 🚀 Step 4: Start the Application

### 4.1 Verify Configuration

The application will log which storage backend it's using:

```bash
cd backend
python main.py
```

Look for these log messages:
```
INFO: Initializing S3 storage backend...
INFO: S3 client initialized for region: us-east-1
INFO: Original bucket: smartcloud-vault-original
INFO: Masked bucket: smartcloud-vault-masked
INFO: Initialized storage manager with backend: S3Storage
```

If S3 credentials are missing, it will fallback to local storage:
```
WARNING: AWS credentials not configured. Falling back to local storage.
INFO: Using local file storage backend
```

### 4.2 Test Upload

1. Start the backend:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

2. Upload a test file via the API or frontend

3. Check MongoDB for storage metadata:
   ```javascript
   // In MongoDB shell:
   db.files.findOne({}, {
     storage_type: 1,
     original_s3_key: 1,
     masked_s3_key: 1,
     original_bucket: 1,
     masked_bucket: 1
   })
   ```

   Expected output:
   ```json
   {
     "storage_type": "s3",
     "original_s3_key": "CompanyA/abc123-uuid/document.pdf",
     "masked_s3_key": "CompanyA/abc123-uuid/document_masked.pdf",
     "original_bucket": "smartcloud-vault-original",
     "masked_bucket": "smartcloud-vault-masked"
   }
   ```

4. Verify in AWS S3 Console:
   - Go to S3 → `smartcloud-vault-original` → You should see: `CompanyA/abc123-uuid/document.pdf`
   - Go to S3 → `smartcloud-vault-masked` → You should see: `CompanyA/abc123-uuid/document_masked.pdf`

---

## 🔍 Step 5: Verify Access Control

### Test Email Matching

```bash
# Test 1: Upload with email
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test.pdf" \
  -F "company=TestCorp" \
  -F "department=IT" \
  -F "uploader_email=user@example.com"

# Response will include file_id, e.g., "abc-123-uuid"

# Test 2: Download with MATCHING email (should get ORIGINAL)
curl -X POST http://localhost:8000/api/files/access \
  -H "Content-Type: application/json" \
  -d '{"file_id": "abc-123-uuid", "requester_email": "user@example.com"}' \
  --output original.pdf

# Test 3: Download with DIFFERENT email (should get MASKED)
curl -X POST http://localhost:8000/api/files/access \
  -H "Content-Type: application/json" \
  -d '{"file_id": "abc-123-uuid", "requester_email": "other@example.com"}' \
  --output masked.pdf

# Compare the files - they should be different!
```

---

## 🔄 Migration from Local to S3

### Option 1: Fresh Start (Recommended)

1. Set `USE_S3_STORAGE=true` in `.env`
2. Restart the backend
3. All new uploads will use S3
4. Old files remain in local storage (backward compatible)

### Option 2: Migrate Existing Files

Create a migration script (example):

```python
# migrate_to_s3.py
import asyncio
from storage.file_storage import file_storage
from storage.s3_storage import S3Storage
from storage.database import Database
from config import settings

async def migrate_files():
    await Database.connect_db()
    db = Database.db
    
    s3 = S3Storage(
        original_bucket=settings.s3_original_bucket,
        masked_bucket=settings.s3_masked_bucket
    )
    
    # Get all local files
    files = await db.files.find({"storage_type": {"$in": [None, "local"]}}).to_list(None)
    
    for file_doc in files:
        file_id = file_doc['file_id']
        company = file_doc['company']
        filename = file_doc['original_filename']
        
        # Upload original
        original_content = await file_storage.get_file(file_id)
        if original_content:
            result = await s3.save_original(original_content, file_id, filename, company)
            
            # Upload masked
            masked_content = await file_storage.get_masked_file(file_id)
            if masked_content:
                masked_result = await s3.save_masked(masked_content, file_id, filename, company)
                
                # Update MongoDB
                await db.files.update_one(
                    {"file_id": file_id},
                    {"$set": {
                        "storage_type": "s3",
                        "original_s3_key": result['s3_key'],
                        "masked_s3_key": masked_result['s3_key'],
                        "original_bucket": result['bucket'],
                        "masked_bucket": masked_result['bucket']
                    }}
                )
                print(f"Migrated {file_id}")

if __name__ == "__main__":
    asyncio.run(migrate_files())
```

---

## 🛡️ Security Best Practices

### 1. Bucket Security

- ✅ Block all public access
- ✅ Enable encryption at rest (SSE-S3 or SSE-KMS)
- ✅ Enable versioning (for audit trail)
- ✅ Enable access logging
- ✅ Use bucket policies to restrict access

### 2. IAM Security

- ✅ Use least privilege principle
- ✅ Rotate access keys every 90 days
- ✅ Never commit credentials to code
- ✅ Use environment variables or AWS Secrets Manager
- ✅ Enable MFA for IAM user

### 3. Network Security

- ✅ Use VPC endpoints for S3 (if running in AWS)
- ✅ Enable HTTPS-only access
- ✅ Use pre-signed URLs for temporary access

### 4. Monitoring

Set up CloudWatch alarms for:
- Unusual API calls
- Failed access attempts
- Large downloads
- Bucket policy changes

---

## 📊 Cost Estimation

### AWS S3 Pricing (us-east-1, as of 2024)

| Component | Price |
|-----------|-------|
| Storage (first 50 TB) | $0.023/GB/month |
| PUT/POST requests | $0.005 per 1,000 requests |
| GET requests | $0.0004 per 1,000 requests |
| Data transfer OUT | $0.09/GB (first 10 TB) |

**Example:**
- 10,000 documents × 1 MB each = 10 GB storage
- Monthly storage cost: 10 × $0.023 = **$0.23/month**
- Upload requests: 10,000 × $0.005/1000 = **$0.05**
- Download requests: 50,000 × $0.0004/1000 = **$0.02**

**Total: ~$0.30/month for 10,000 documents**

---

## 🐛 Troubleshooting

### Issue: "NoCredentialsError"

**Cause**: AWS credentials not found

**Solution**:
1. Check `.env` file has `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
2. Verify credentials are correct
3. Check file permissions on `.env`

### Issue: "Access Denied" when uploading

**Cause**: IAM user lacks S3 permissions

**Solution**:
1. Verify IAM policy includes `s3:PutObject`
2. Check bucket names match configuration
3. Verify bucket exists in the correct region

### Issue: "Bucket does not exist"

**Cause**: Bucket name mismatch or wrong region

**Solution**:
1. Verify bucket names in `.env` match AWS
2. Check `AWS_REGION` matches bucket region
3. List buckets: `aws s3 ls`

### Issue: Files not appearing in S3

**Cause**: Application using local storage

**Solution**:
1. Check logs for storage backend initialization
2. Verify `USE_S3_STORAGE=true` in `.env`
3. Restart the application

---

## ✅ Validation Checklist

After setup, verify:

- [ ] S3 buckets created with correct names
- [ ] Buckets have public access BLOCKED
- [ ] Buckets have encryption enabled
- [ ] IAM user has correct permissions
- [ ] `.env` file configured with AWS credentials
- [ ] `USE_S3_STORAGE=true` in `.env`
- [ ] Backend logs show "S3Storage" initialization
- [ ] Test upload creates files in both buckets
- [ ] MongoDB stores S3 keys in metadata
- [ ] Email match returns original file
- [ ] Email mismatch returns masked file
- [ ] Files are encrypted at rest (check S3 properties)

---

## 🔄 Switching Back to Local Storage

If you need to switch back:

1. Set `USE_S3_STORAGE=false` in `.env`
2. Restart the backend
3. New uploads will use local storage
4. S3 files remain accessible (backward compatible)

---

## 📚 Additional Resources

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [IAM Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)

---

## 🆘 Support

If you encounter issues:

1. Check application logs: `backend/logs/`
2. Review CloudWatch logs (if using AWS)
3. Verify bucket permissions
4. Test AWS credentials: `aws s3 ls`

---

**✅ Setup Complete!**

Your SmartCloud Vault is now using AWS S3 for scalable, secure document storage with automatic access control based on email matching.
