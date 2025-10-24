import requests
import sys
import json
from datetime import datetime

class PrescriptionAPITester:
    def __init__(self, base_url="https://prescriptify-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text}")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text
                })

            return success, response.json() if success and response.content else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_login(self):
        """Test doctor login"""
        success, response = self.run_test(
            "Doctor Login",
            "POST",
            "auth/login",
            200,
            data={"username": "doctor", "password": "doctor123"}
        )
        if success and 'token' in response:
            self.token = response['token']
            print(f"   Token received: {self.token[:20]}...")
            return True
        return False

    def test_invalid_login(self):
        """Test invalid login credentials"""
        success, response = self.run_test(
            "Invalid Login",
            "POST",
            "auth/login",
            401,
            data={"username": "invalid", "password": "wrong"}
        )
        return success

    def test_medicine_search(self):
        """Test medicine search functionality"""
        # Test search without query
        success1, response1 = self.run_test(
            "Medicine Search - All",
            "GET",
            "medicines/search",
            200
        )
        
        # Test search with query
        success2, response2 = self.run_test(
            "Medicine Search - Query",
            "GET",
            "medicines/search?q=para",
            200
        )
        
        return success1 and success2

    def test_create_prescription(self):
        """Test prescription creation"""
        prescription_data = {
            "patient_name": "John Doe",
            "patient_age": 35,
            "date": "2024-01-15",
            "medicines": [
                {
                    "name": "Paracetamol",
                    "dosage": "500mg",
                    "frequency": "Twice daily"
                },
                {
                    "name": "Ibuprofen",
                    "dosage": "400mg",
                    "frequency": "Once daily"
                }
            ],
            "doctor_notes": "Take after meals. Complete the course."
        }
        
        success, response = self.run_test(
            "Create Prescription",
            "POST",
            "prescriptions",
            200,
            data=prescription_data
        )
        
        if success and 'id' in response:
            self.prescription_id = response['id']
            print(f"   Prescription ID: {self.prescription_id}")
            return True
        return False

    def test_get_prescriptions(self):
        """Test getting all prescriptions"""
        success, response = self.run_test(
            "Get All Prescriptions",
            "GET",
            "prescriptions",
            200
        )
        return success

    def test_search_prescriptions(self):
        """Test prescription search by patient name"""
        success, response = self.run_test(
            "Search Prescriptions",
            "GET",
            "prescriptions?patient_name=John",
            200
        )
        return success

    def test_get_prescription_by_id(self):
        """Test getting specific prescription"""
        if not hasattr(self, 'prescription_id'):
            print("❌ Skipping - No prescription ID available")
            return False
            
        success, response = self.run_test(
            "Get Prescription by ID",
            "GET",
            f"prescriptions/{self.prescription_id}",
            200
        )
        return success

    def test_download_prescription_pdf(self):
        """Test PDF download"""
        if not hasattr(self, 'prescription_id'):
            print("❌ Skipping - No prescription ID available")
            return False
            
        url = f"{self.api_url}/prescriptions/{self.prescription_id}/pdf"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        print(f"\n🔍 Testing PDF Download...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            success = response.status_code == 200 and response.headers.get('content-type') == 'application/pdf'
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - PDF downloaded successfully")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                self.failed_tests.append({
                    "test": "PDF Download",
                    "expected": "200 with PDF content",
                    "actual": f"{response.status_code} with {response.headers.get('content-type')}"
                })
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": "PDF Download",
                "error": str(e)
            })
            self.tests_run += 1
            return False

    def test_unauthorized_access(self):
        """Test unauthorized access"""
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Unauthorized Access",
            "GET",
            "prescriptions",
            401
        )
        
        # Restore token
        self.token = original_token
        return success

def main():
    print("🏥 Starting Prescription Management API Tests")
    print("=" * 60)
    
    tester = PrescriptionAPITester()
    
    # Test sequence
    tests = [
        ("Login Authentication", tester.test_login),
        ("Invalid Login", tester.test_invalid_login),
        ("Medicine Search", tester.test_medicine_search),
        ("Create Prescription", tester.test_create_prescription),
        ("Get All Prescriptions", tester.test_get_prescriptions),
        ("Search Prescriptions", tester.test_search_prescriptions),
        ("Get Prescription by ID", tester.test_get_prescription_by_id),
        ("Download PDF", tester.test_download_prescription_pdf),
        ("Unauthorized Access", tester.test_unauthorized_access),
    ]
    
    # Run tests
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")
            tester.failed_tests.append({
                "test": test_name,
                "error": f"Test crashed: {str(e)}"
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 Test Summary")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ Failed Tests:")
        for failure in tester.failed_tests:
            print(f"   - {failure['test']}: {failure.get('error', f\"Expected {failure.get('expected')}, got {failure.get('actual')}\")}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())