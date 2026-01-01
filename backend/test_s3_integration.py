"""
AWS S3 Integration - Validation Test Script

This script tests the S3 storage integration to ensure everything is working correctly.
Run this after setting up S3 to verify the configuration.

Usage:
    python test_s3_integration.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from storage.storage_factory import storage_manager
from storage.s3_storage import S3Storage
from config import settings


class S3IntegrationTester:
    """Test suite for S3 integration."""
    
    def __init__(self):
        self.test_file_id = "test-integration-12345"
        self.test_company = "TestCompany"
        self.test_filename = "integration_test.txt"
        self.test_content = b"Hello from SmartCloud Vault S3 Integration Test!"
        self.passed = 0
        self.failed = 0
    
    def log_test(self, name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
        if message:
            print(f"       {message}")
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print("\n" + "="*60)
        print(f"Test Summary: {self.passed}/{total} passed")
        if self.failed == 0:
            print("✅ All tests passed! S3 integration is working correctly.")
        else:
            print(f"❌ {self.failed} test(s) failed. Please review the setup.")
        print("="*60)
    
    async def test_configuration(self):
        """Test 1: Verify S3 configuration."""
        print("\n📋 Test 1: Configuration")
        print("-" * 60)
        
        # Check if S3 is enabled
        is_s3_enabled = settings.use_s3_storage
        self.log_test(
            "S3 storage enabled",
            is_s3_enabled,
            f"USE_S3_STORAGE = {settings.use_s3_storage}"
        )
        
        # Check AWS credentials
        has_credentials = bool(settings.aws_access_key_id and settings.aws_secret_access_key)
        self.log_test(
            "AWS credentials configured",
            has_credentials,
            "Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env"
        )
        
        # Check bucket names
        has_buckets = bool(settings.s3_original_bucket and settings.s3_masked_bucket)
        self.log_test(
            "S3 bucket names configured",
            has_buckets,
            f"Original: {settings.s3_original_bucket}, Masked: {settings.s3_masked_bucket}"
        )
        
        # Check region
        has_region = bool(settings.aws_region)
        self.log_test(
            "AWS region configured",
            has_region,
            f"Region: {settings.aws_region}"
        )
        
        return is_s3_enabled and has_credentials and has_buckets and has_region
    
    async def test_storage_backend(self):
        """Test 2: Verify storage backend initialization."""
        print("\n🔧 Test 2: Storage Backend")
        print("-" * 60)
        
        backend_type = type(storage_manager.backend).__name__
        is_s3 = backend_type == "S3Storage"
        
        self.log_test(
            "Storage backend type",
            is_s3 if settings.use_s3_storage else backend_type == "LocalStorage",
            f"Backend: {backend_type}"
        )
        
        return is_s3 if settings.use_s3_storage else True
    
    async def test_upload_original(self):
        """Test 3: Upload original file to S3."""
        print("\n📤 Test 3: Upload Original File")
        print("-" * 60)
        
        try:
            result = await storage_manager.save_original(
                file_content=self.test_content,
                file_id=self.test_file_id,
                filename=self.test_filename,
                company=self.test_company
            )
            
            # Verify result structure
            has_storage_type = 'storage_type' in result
            has_s3_key = 's3_key' in result or 'path' in result
            
            self.log_test(
                "Upload original file",
                has_storage_type and has_s3_key,
                f"Storage type: {result.get('storage_type')}"
            )
            
            if settings.use_s3_storage:
                s3_key = result.get('s3_key')
                expected_key_pattern = f"{self.test_company}/{self.test_file_id}"
                has_correct_key = expected_key_pattern in str(s3_key)
                
                self.log_test(
                    "S3 key format correct",
                    has_correct_key,
                    f"S3 Key: {s3_key}"
                )
                
                self.s3_original_key = s3_key
            
            return True
        
        except Exception as e:
            self.log_test("Upload original file", False, f"Error: {e}")
            return False
    
    async def test_upload_masked(self):
        """Test 4: Upload masked file to S3."""
        print("\n📤 Test 4: Upload Masked File")
        print("-" * 60)
        
        try:
            masked_content = b"[MASKED] Sensitive data has been redacted"
            
            result = await storage_manager.save_masked(
                file_content=masked_content,
                file_id=self.test_file_id,
                filename=self.test_filename,
                company=self.test_company
            )
            
            has_storage_type = 'storage_type' in result
            has_s3_key = 's3_key' in result or 'path' in result
            
            self.log_test(
                "Upload masked file",
                has_storage_type and has_s3_key,
                f"Storage type: {result.get('storage_type')}"
            )
            
            if settings.use_s3_storage:
                s3_key = result.get('s3_key')
                expected_pattern = f"{self.test_company}/{self.test_file_id}"
                has_correct_key = expected_pattern in str(s3_key)
                
                self.log_test(
                    "Masked S3 key format correct",
                    has_correct_key,
                    f"S3 Key: {s3_key}"
                )
                
                self.s3_masked_key = s3_key
            
            return True
        
        except Exception as e:
            self.log_test("Upload masked file", False, f"Error: {e}")
            return False
    
    async def test_download_original(self):
        """Test 5: Download original file from S3."""
        print("\n📥 Test 5: Download Original File")
        print("-" * 60)
        
        try:
            storage_key = getattr(self, 's3_original_key', None)
            
            content = await storage_manager.get_original(
                file_id=self.test_file_id,
                storage_key=storage_key
            )
            
            has_content = content is not None
            self.log_test(
                "Download original file",
                has_content,
                f"Retrieved {len(content)} bytes" if has_content else "No content retrieved"
            )
            
            if has_content:
                content_matches = content == self.test_content
                self.log_test(
                    "Content matches uploaded",
                    content_matches,
                    "Content verification successful"
                )
                return content_matches
            
            return False
        
        except Exception as e:
            self.log_test("Download original file", False, f"Error: {e}")
            return False
    
    async def test_download_masked(self):
        """Test 6: Download masked file from S3."""
        print("\n📥 Test 6: Download Masked File")
        print("-" * 60)
        
        try:
            storage_key = getattr(self, 's3_masked_key', None)
            
            content = await storage_manager.get_masked(
                file_id=self.test_file_id,
                storage_key=storage_key
            )
            
            has_content = content is not None
            self.log_test(
                "Download masked file",
                has_content,
                f"Retrieved {len(content)} bytes" if has_content else "No content retrieved"
            )
            
            if has_content:
                is_different = content != self.test_content
                self.log_test(
                    "Masked content differs from original",
                    is_different,
                    "Verification successful"
                )
                return is_different
            
            return False
        
        except Exception as e:
            self.log_test("Download masked file", False, f"Error: {e}")
            return False
    
    async def test_cleanup(self):
        """Test 7: Cleanup test files."""
        print("\n🧹 Test 7: Cleanup")
        print("-" * 60)
        
        try:
            storage_key_original = getattr(self, 's3_original_key', None)
            storage_key_masked = getattr(self, 's3_masked_key', None)
            
            # Delete original
            deleted_original = await storage_manager.delete_original(
                file_id=self.test_file_id,
                storage_key=storage_key_original
            )
            
            self.log_test(
                "Delete original file",
                deleted_original,
                "Original test file cleaned up"
            )
            
            # Delete masked
            deleted_masked = await storage_manager.delete_masked(
                file_id=self.test_file_id,
                storage_key=storage_key_masked
            )
            
            self.log_test(
                "Delete masked file",
                deleted_masked,
                "Masked test file cleaned up"
            )
            
            return deleted_original and deleted_masked
        
        except Exception as e:
            self.log_test("Cleanup", False, f"Error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests in sequence."""
        print("\n" + "="*60)
        print("🧪 SmartCloud Vault - S3 Integration Tests")
        print("="*60)
        
        # Run tests
        config_ok = await self.test_configuration()
        
        if not config_ok:
            print("\n⚠️  Configuration incomplete. Please review setup.")
            self.print_summary()
            return False
        
        backend_ok = await self.test_storage_backend()
        
        if backend_ok:
            await self.test_upload_original()
            await self.test_upload_masked()
            await self.test_download_original()
            await self.test_download_masked()
            await self.test_cleanup()
        
        self.print_summary()
        
        return self.failed == 0


async def main():
    """Main test runner."""
    tester = S3IntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 S3 integration is fully functional!")
        print("\nNext steps:")
        print("1. Upload a file via the API")
        print("2. Check S3 console to verify files appear")
        print("3. Test download with matching/non-matching emails")
        return 0
    else:
        print("\n❗ Some tests failed. Please review:")
        print("1. Check .env configuration")
        print("2. Verify AWS credentials")
        print("3. Ensure S3 buckets exist")
        print("4. Check IAM permissions")
        print("\nSee AWS_S3_SETUP_GUIDE.md for detailed instructions.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
