# Employee-Aware Upload & Role-Based Download System

## Overview

SmartCloud Vault now supports **employee-centric file organization** and **role-based access control** for enhanced security and compliance.

### Key Features

1. **Employee-Aware Uploads**: Files are organized by employee ID in AWS S3
2. **Role-Based Downloads**: Different access levels for employees vs company authorities
3. **Dual-Bucket Storage**: Original files (employee access) and masked files (authority access)
4. **Access Validation**: Strict employee credential verification

---

## Architecture Changes

### S3 Folder Structure

**Previous Structure:**
```
s3://smartcloud-vault-original/
├── CompanyA/
│   ├── file-id-123/
│   │   └── document.pdf
```

**New Structure:**
```
s3://smartcloud-vault-original/
├── EMP12345/
│   ├── aadhaar.pdf
│   ├── pan_card.jpg
│   └── passport.pdf
├── EMP67890/
│   └── driving_license.pdf
```

### MongoDB Schema Updates

```python
class FileMetadata(BaseModel):
    # Existing fields...
    company: str
    department: Department
    uploader_email: str
    uploader_name: Optional[str]
    
    # NEW: Employee fields
    employee_id: Optional[str] = None          # Required for uploads
    employee_name: Optional[str] = None        # Required for uploads
    employee_email: Optional[str] = None       # Required for uploads
    document_name: Optional[str] = None        # Optional (e.g., "Aadhaar", "PAN")
```

---

## Upload Process

### Frontend Upload Form

New required fields:
- **Employee ID**: Used as folder name in S3 (e.g., `EMP12345`)
- **Employee Name**: For validation during download
- **Employee Email**: For employee access verification
- **Document Name**: Optional document type (e.g., "Aadhaar", "PAN Card")

### Backend Upload Endpoint

**Endpoint:** `POST /api/upload`

**Form Data:**
```
file: <binary>
company: "TechCorp"
department: "HR"
uploader_email: "hr@company.com"
uploader_name: "HR Manager"
employee_id: "EMP12345"          # NEW - Required
employee_name: "John Doe"        # NEW - Required
employee_email: "john@company.com" # NEW - Required
document_name: "Aadhaar Card"    # NEW - Optional
```

**S3 Key Generation:**
```python
# Old: "{company}/{file_id}/{filename}"
# New: "{employee_id}/{filename}"
s3_key = f"{employee_id}/{filename}"
```

---

## Download Process

### Two Access Modes

#### 1. Employee Access (Original Files)

**Use Case:** Employees accessing their own files

**Endpoint:** `POST /api/files/employee/access`

**Request:**
```json
{
  "employee_id": "EMP12345",
  "employee_name": "John Doe",
  "employee_email": "john@company.com",
  "file_id": "file-id-abc123"
}
```

**Validation:**
- Employee ID must match file records
- Employee name must match (case-insensitive)
- Employee email must match (case-insensitive)

**Returns:** Original file from `s3://smartcloud-vault-original/{employee_id}/`

**HTTP Headers:**
```
X-File-Type: original
X-Access-Type: employee
X-Employee-ID: EMP12345
```

---

#### 2. Authority Access (Masked Files)

**Use Case:** HR/Admin/Auditor accessing employee files

**Endpoint:** `POST /api/files/authority/access`

**Request:**
```json
{
  "name": "Jane Smith",
  "email": "jane.smith@company.com",
  "role": "HR",
  "employee_id": "EMP12345",
  "file_id": "file-id-abc123"
}
```

**Allowed Roles:**
- `HR`: Human Resources personnel
- `ADMIN`: System administrators
- `AUDITOR`: Compliance auditors

**Validation:**
- Role must be HR/ADMIN/AUDITOR
- Employee ID must match file records

**Returns:** Masked file from `s3://smartcloud-vault-masked/{employee_id}/`

**HTTP Headers:**
```
X-File-Type: masked
X-Access-Type: authority
X-Authority-Role: HR
X-Employee-ID: EMP12345
```

---

## Frontend UI

### Upload Page (`/`)

New Employee Information Section:
```
┌─────────────────────────────────────────┐
│ Employee Information                    │
├─────────────────────────────────────────┤
│ Employee ID *       [ EMP12345        ] │
│ Employee Name *     [ John Doe        ] │
│ Employee Email *    [ john@company.com] │
│ Document Type       [ Aadhaar Card    ] │
└─────────────────────────────────────────┘
```

### Download Page (`/download-role`)

Role Selection:
```
┌──────────────────┐  ┌──────────────────┐
│    Employee      │  │ Company Authority│
│   👤 Access      │  │   🛡️ Access      │
│                  │  │                  │
│ Your own files   │  │ Employee files   │
│ (Original)       │  │ (Masked)         │
└──────────────────┘  └──────────────────┘
```

**Employee Form:**
- Employee ID
- Employee Name
- Employee Email
- File ID
- **List Files** button (shows all files for employee)

**Authority Form:**
- Your Name
- Your Email
- Your Role (HR/Admin/Auditor)
- Employee ID (target)
- File ID

---

## API Endpoints

### 1. Upload File
```http
POST /api/upload
Content-Type: multipart/form-data

file: <binary>
company: string
department: string
uploader_email: string
uploader_name: string (optional)
employee_id: string (required)
employee_name: string (required)
employee_email: string (required)
document_name: string (optional)
```

### 2. Employee Access File
```http
POST /api/files/employee/access
Content-Type: application/json

{
  "employee_id": "EMP12345",
  "employee_name": "John Doe",
  "employee_email": "john@company.com",
  "file_id": "file-id-abc123"
}

Response: Original file (binary)
Headers:
  X-File-Type: original
  X-Access-Type: employee
```

### 3. Authority Access File
```http
POST /api/files/authority/access
Content-Type: application/json

{
  "name": "Jane Smith",
  "email": "jane.smith@company.com",
  "role": "HR",
  "employee_id": "EMP12345",
  "file_id": "file-id-abc123"
}

Response: Masked file (binary)
Headers:
  X-File-Type: masked
  X-Access-Type: authority
  X-Authority-Role: HR
```

### 4. List Employee Files
```http
GET /api/files/employee/files/{employee_id}

Response:
{
  "employee_id": "EMP12345",
  "employee_name": "John Doe",
  "employee_email": "john@company.com",
  "files": [
    {
      "file_id": "abc123",
      "original_filename": "aadhaar.pdf",
      "document_name": "Aadhaar Card",
      "upload_date": "2024-01-15T10:30:00",
      "file_size": 204800,
      "classification": "Restricted",
      "is_protected": true,
      "masked_fields": ["aadhaar_number", "name"]
    }
  ],
  "total_count": 1
}
```

---

## Security Features

### Access Control Matrix

| Role      | Access Type | Bucket           | File Version |
|-----------|-------------|------------------|--------------|
| Employee  | Own files   | Original         | Original     |
| HR        | Any employee| Masked           | Masked       |
| Admin     | Any employee| Masked           | Masked       |
| Auditor   | Any employee| Masked           | Masked       |

### Validation Rules

**Employee Access:**
1. Employee ID must exist in database
2. Employee name must match exactly (case-insensitive)
3. Employee email must match exactly (case-insensitive)
4. File must belong to the employee

**Authority Access:**
1. Role must be HR, ADMIN, or AUDITOR
2. Target employee ID must exist
3. File must belong to target employee
4. Always returns masked version

### Error Responses

```http
403 Forbidden - "Employee ID does not match file records"
403 Forbidden - "Employee name does not match file records"
403 Forbidden - "Employee email does not match file records"
403 Forbidden - "Invalid role for authority access"
404 Not Found - "File not found"
400 Bad Request - "File does not have employee information"
```

---

## Backward Compatibility

### Legacy Email-Based Access

The original email-based access endpoint remains functional:

```http
POST /api/files/access
{
  "file_id": "abc123",
  "requester_email": "user@company.com"
}
```

**Rules:**
- If email matches uploader → original file
- If email doesn't match → masked file

This endpoint is preserved for backward compatibility but **does not** use the new role-based system.

---

## Migration Guide

### Existing Files

Files uploaded before this update:
- Will not have employee fields (`employee_id`, `employee_name`, `employee_email`)
- Can still be accessed via legacy email-based endpoint
- Cannot be accessed via new role-based endpoints (will return error: "File does not have employee information")

### New Files

All new uploads must include:
- Employee ID (mandatory)
- Employee Name (mandatory)
- Employee Email (mandatory)

---

## Configuration

No new environment variables required. Uses existing S3 configuration:

```env
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_ORIGINAL_BUCKET=smartcloud-vault-original
S3_MASKED_BUCKET=smartcloud-vault-masked
```

---

## Testing

### Upload Test

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test.pdf" \
  -F "company=TechCorp" \
  -F "department=HR" \
  -F "uploader_email=hr@company.com" \
  -F "uploader_name=HR Manager" \
  -F "employee_id=EMP12345" \
  -F "employee_name=John Doe" \
  -F "employee_email=john@company.com" \
  -F "document_name=Aadhaar Card"
```

### Employee Access Test

```bash
curl -X POST http://localhost:8000/api/files/employee/access \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP12345",
    "employee_name": "John Doe",
    "employee_email": "john@company.com",
    "file_id": "abc123"
  }' \
  --output original_file.pdf
```

### Authority Access Test

```bash
curl -X POST http://localhost:8000/api/files/authority/access \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane.smith@company.com",
    "role": "HR",
    "employee_id": "EMP12345",
    "file_id": "abc123"
  }' \
  --output masked_file.pdf
```

### List Files Test

```bash
curl http://localhost:8000/api/files/employee/files/EMP12345
```

---

## Compliance Benefits

1. **Data Minimization**: Authorities only see masked data
2. **Audit Trail**: All access logged with role and user info
3. **Separation of Concerns**: Employee data organized by employee ID
4. **GDPR Compliance**: Employees can access their own data
5. **Role-Based Access**: Clear separation between employee and authority access

---

## Future Enhancements

- [ ] Real-time access audit logs
- [ ] Employee authentication integration (OAuth/LDAP)
- [ ] Granular role permissions (e.g., HR can only access specific departments)
- [ ] File expiration policies per employee
- [ ] Bulk download for authorities
- [ ] Activity dashboard for employees

---

## Support

For issues or questions:
1. Check error messages in browser console/network tab
2. Verify employee credentials match upload records exactly
3. Ensure role is HR/ADMIN/AUDITOR for authority access
4. Check backend logs for detailed error messages

---

**Last Updated:** January 2025  
**Version:** 2.0.0
