import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:5000"  # Change to your deployed URL
TEST_FILES_DIR = "../"  # Directory containing test CV files

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_process_cv():
    """Test CV processing with a sample file"""
    print("\n📄 Testing CV processing...")
    
    # Create a sample CV text file for testing
    sample_cv = """
    NGUYỄN VĂN TEST
    
    Thông tin cá nhân:
    Email: test@example.com
    Điện thoại: 0987654321
    Ngày sinh: 15/05/1995
    Giới tính: Nam
    
    Học vấn: Đại học
    Trường: Đại học Bách Khoa Hà Nội
    Chuyên ngành: Công nghệ thông tin
    
    Vị trí ứng tuyển: Senior Developer
    Kinh nghiệm: 5 năm kinh nghiệm lập trình
    """
    
    # Save as temporary file
    test_file = "test_cv.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(sample_cv)
    
    try:
        with open(test_file, "rb") as f:
            files = {"file": ("test_cv.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/process-cv", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ CV processing successful!")
            print(f"📊 Extracted fields: {len(data['fields'])}")
            
            # Print extracted fields
            for field, value in data['fields'].items():
                if value:
                    confidence = data['confidence'].get(field, 0) * 100
                    print(f"  • {field}: {value} ({confidence:.0f}%)")
            
            return True
        else:
            print(f"❌ CV processing failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ CV processing error: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

def test_verify_field():
    """Test field verification"""
    print("\n✅ Testing field verification...")
    
    test_data = {
        "field": "email",
        "value": "test@example.com",
        "rawContent": "Email: test@example.com"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/verify-field",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Field verification successful: {data['verified']}")
            return True
        else:
            print(f"❌ Field verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Field verification error: {e}")
        return False

def test_save_cv():
    """Test CV data saving"""
    print("\n💾 Testing CV data saving...")
    
    test_data = {
        "fields": {
            "name": "Test User",
            "email": "test@example.com"
        },
        "confidence": {
            "name": 0.95,
            "email": 0.9
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/save-cv",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ CV saving successful: {data['cv_id']}")
            return True
        else:
            print(f"❌ CV saving failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CV saving error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 CV Reader Backend API Tests")
    print("=" * 40)
    print(f"Testing API at: {BASE_URL}")
    print()
    
    tests = [
        test_health,
        test_process_cv,
        test_verify_field,
        test_save_cv
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        print("\n💡 Next steps:")
        print("1. Update frontend API_BASE_URL to your deployed URL")
        print("2. Test with real CV files")
        print("3. Monitor API performance")
    else:
        print("❌ Some tests failed. Please check the API configuration.")

if __name__ == "__main__":
    main()