"""Test script to check employee file filtering."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

async def test_employee_query():
    """Test if employee_id filtering works correctly."""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]
    
    print("Testing employee file query...")
    print("=" * 60)
    
    # First, let's see all files in the database
    print("\n1. All files in database:")
    all_files = await db.files.find({}).to_list(length=None)
    print(f"Total files: {len(all_files)}")
    for file_doc in all_files:
        print(f"  - File ID: {file_doc.get('file_id')}")
        print(f"    Employee ID: {file_doc.get('employee_id')}")
        print(f"    Employee Name: {file_doc.get('employee_name')}")
        print(f"    Filename: {file_doc.get('original_filename')}")
        print()
    
    # Now test filtering by specific employee_id
    test_employee_id = "emp23456"
    print(f"\n2. Files for employee_id = '{test_employee_id}':")
    cursor = db.files.find({"employee_id": test_employee_id})
    employee_files = await cursor.to_list(length=None)
    print(f"Found {len(employee_files)} file(s)")
    for file_doc in employee_files:
        print(f"  - File ID: {file_doc.get('file_id')}")
        print(f"    Filename: {file_doc.get('original_filename')}")
        print()
    
    # Test case-insensitive search
    print(f"\n3. Testing case-insensitive search for 'EMP23456':")
    cursor_ci = db.files.find({"employee_id": {"$regex": f"^{test_employee_id}$", "$options": "i"}})
    employee_files_ci = await cursor_ci.to_list(length=None)
    print(f"Found {len(employee_files_ci)} file(s)")
    
    # Close connection
    client.close()
    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == "__main__":
    asyncio.run(test_employee_query())
