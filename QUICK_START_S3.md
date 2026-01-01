# 🚀 Quick Start - AWS S3 Integration

## For Users Who Want to Get Started Immediately

This guide gets you up and running with S3 storage in **under 15 minutes**.

---

## ⚡ Super Quick Setup (5 Steps)

### Step 1: AWS Account Setup (5 min)

1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to **IAM** → **Users** → **Create user**
3. Name: `smartcloud-s3-user`
4. Click **Next**, then **Attach policies directly**
5. Search and select: `AmazonS3FullAccess` (for testing, restrict later)
6. Click **Create user**
7. Click on the user → **Security credentials** → **Create access key**
8. Select **Application running outside AWS**
9. **SAVE** your Access Key ID and Secret Access Key (you'll need them!)

### Step 2: Create S3 Buckets (2 min)

**Option A - AWS Console (Easiest):**

1. Go to **S3** → **Create bucket**
2. Bucket name: `smartcloud-vault-original`
3. Region: `us-east-1` (or your preferred)
4. **Block all public access**: ✅ CHECK THIS!
5. Click **Create bucket**
6. Repeat for: `smartcloud-vault-masked`

**Option B - AWS CLI (Fastest):**

```bash
aws s3 mb s3://smartcloud-vault-original --region us-east-1
aws s3 mb s3://smartcloud-vault-masked --region us-east-1
```

### Step 3: Configure Backend (3 min)

Create/edit `backend/.env`:

```bash
# Enable S3
USE_S3_STORAGE=true

# AWS Credentials (paste your keys from Step 1)
AWS_ACCESS_KEY_ID=AKIA...your-key...
AWS_SECRET_ACCESS_KEY=abc...your-secret...
AWS_REGION=us-east-1

# Bucket names (must match Step 2)
S3_ORIGINAL_BUCKET=smartcloud-vault-original
S3_MASKED_BUCKET=smartcloud-vault-masked

# Keep existing settings
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=smartcloud_vault
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Step 4: Install Dependencies (2 min)

```bash
cd backend
pip install boto3 botocore
# Or install all requirements:
pip install -r requirements.txt
```

### Step 5: Start & Test (3 min)

```bash
# Start the backend
python main.py

# Look for this in logs:
# ✅ "Initialized storage manager with backend: S3Storage"
# ✅ "S3 client initialized for region: us-east-1"
```

**Test it:**

```bash
# Run validation tests
python test_s3_integration.py

# Should see:
# ✅ All tests passed! S3 integration is working correctly.
```

---

## ✅ That's It!

Your SmartCloud Vault now uses AWS S3 for storage!

**What changed:**
- Files are now stored in S3 (not local disk)
- Everything else works exactly the same

**What didn't change:**
- API endpoints (same URLs)
- Upload process (same flow)
- Access control (same email logic)
- Frontend (no changes needed)

---

## 🧪 Quick Verification

### Test 1: Upload a File

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test.pdf" \
  -F "company=TestCorp" \
  -F "department=IT" \
  -F "uploader_email=user@example.com"
```

### Test 2: Check S3

Go to AWS S3 Console → `smartcloud-vault-original`

You should see: `TestCorp/[file-id]/test.pdf`

### Test 3: Download Original (Matching Email)

```bash
curl -X POST http://localhost:8000/api/files/access \
  -H "Content-Type: application/json" \
  -d '{"file_id": "[file-id]", "requester_email": "user@example.com"}' \
  --output original.pdf
```

### Test 4: Download Masked (Different Email)

```bash
curl -X POST http://localhost:8000/api/files/access \
  -H "Content-Type: application/json" \
  -d '{"file_id": "[file-id]", "requester_email": "other@example.com"}' \
  --output masked.pdf
```

**Compare the files - they should be different!**

---

## 🐛 Troubleshooting

### "NoCredentialsError"

**Fix:** Check your `.env` file has `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

### "BucketNotFound"

**Fix:** 
1. Check bucket names match in `.env` and AWS Console
2. Verify region: `AWS_REGION=us-east-1`

### Still Using Local Storage

**Fix:** 
1. Check `.env` has `USE_S3_STORAGE=true` (lowercase)
2. Restart the backend
3. Check logs for "S3Storage"

---

## 🔄 Switch Back to Local

Don't like S3? Easy to switch back:

```bash
# In .env:
USE_S3_STORAGE=false

# Restart backend
```

Done! Now using local storage again.

---

## 📚 Need More Details?

- **Complete Setup:** See `AWS_S3_SETUP_GUIDE.md`
- **Code Examples:** See `S3_DEVELOPER_GUIDE.md`
- **Architecture:** See `S3_IMPLEMENTATION_SUMMARY.md`

---

## 🎯 Production Checklist

Before deploying to production:

- [ ] Use restrictive IAM policy (not FullAccess)
- [ ] Enable S3 bucket versioning
- [ ] Enable S3 access logging
- [ ] Use different AWS credentials for production
- [ ] Enable MFA on IAM user
- [ ] Rotate keys every 90 days
- [ ] Review S3 bucket policies
- [ ] Set up CloudWatch alarms
- [ ] Test backup/restore procedures

---

## 💰 Cost Estimate

**For 10,000 documents × 1 MB each:**

- Storage: $0.23/month
- Requests: $0.07/month
- **Total: ~$0.30/month**

S3 is very affordable! 🎉

---

## 🆘 Support

**Issues?**

1. Check logs: `backend/logs/`
2. Run tests: `python test_s3_integration.py`
3. Review guides in docs/

**Still stuck?**

1. Verify AWS credentials: `aws s3 ls`
2. Check IAM permissions
3. Review CloudWatch logs

---

**✅ You're all set! Enjoy scalable cloud storage with SmartCloud Vault!**
