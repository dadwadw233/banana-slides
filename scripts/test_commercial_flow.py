#!/usr/bin/env python3
"""
End-to-end test for commercial features
Tests the complete flow: register -> check quota -> generate images -> verify quota consumption
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:5000/api"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_success(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

class CommercialTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.project_id = None
        self.email = f"test_{int(time.time())}@gmail.com"
        self.password = "Test123456"

    def register(self):
        """Test user registration"""
        print_section("1. Testing User Registration")

        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": self.email,
                "password": self.password,
                "username": f"testuser_{int(time.time())}"
            }
        )

        if response.status_code == 201:
            data = response.json()
            self.token = data['data']['access_token']
            self.user_id = data['data']['user']['id']
            quota = data['data']['user']['quota_balance']

            print_success(f"User registered successfully")
            print_info(f"User ID: {self.user_id}")
            print_info(f"Initial quota: {quota} times")

            if quota == 3:
                print_success("Initial quota is correct (3 times)")
            else:
                print_error(f"Expected 3 free quota, got {quota}")
                return False

            return True
        else:
            print_error(f"Registration failed: {response.text}")
            return False

    def get_quota_balance(self):
        """Get current quota balance"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/quota/balance", headers=headers)

        if response.status_code == 200:
            balance = response.json()['data']['balance']
            return balance
        else:
            print_error(f"Failed to get quota: {response.text}")
            return None

    def create_project(self):
        """Create a test project"""
        print_section("2. Creating Test Project")

        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{BASE_URL}/projects",
            headers=headers,
            json={
                "creation_type": "idea",
                "idea_prompt": "Create a presentation about AI development with 3 slides",
                "language": "zh"
            }
        )

        data = response.json()
        if response.status_code in [200, 201] and data.get('success'):
            # API returns project_id directly in data
            self.project_id = data['data'].get('project_id') or data['data'].get('project', {}).get('id')
            if not self.project_id:
                print_error(f"No project ID in response: {data}")
                return False
            print_success(f"Project created: {self.project_id}")
            return True
        else:
            print_error(f"Failed to create project (status={response.status_code}): {response.text}")
            return False

    def generate_outline(self):
        """Generate project outline"""
        print_section("3. Generating Outline")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{BASE_URL}/projects/{self.project_id}/generate/outline",
            headers=headers,
            json={}
        )

        if response.status_code == 200:
            data = response.json()
            pages = data['data']['pages']
            print_success(f"Outline generated: {len(pages)} pages")
            return True
        else:
            print_error(f"Failed to generate outline: {response.text}")
            return False

    def test_quota_check(self):
        """Test quota check before generation"""
        print_section("4. Testing Quota Check")

        balance_before = self.get_quota_balance()
        print_info(f"Current quota: {balance_before} times")

        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{BASE_URL}/quota/check",
            headers=headers,
            json={
                "action": "generate_image",
                "required_quota": 1
            }
        )

        if response.status_code == 200:
            data = response.json()['data']
            if data['sufficient']:
                print_success(f"Quota check passed (need 1, have {balance_before})")
                return True
            else:
                print_error("Quota check failed unexpectedly")
                return False
        else:
            print_error(f"Quota check request failed: {response.text}")
            return False

    def generate_single_image(self, page_id):
        """Generate image for a single page"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # First generate description
        response = requests.post(
            f"{BASE_URL}/projects/{self.project_id}/pages/{page_id}/generate/description",
            headers=headers,
            json={}
        )

        if response.status_code != 200:
            print_error(f"Failed to generate description: {response.text}")
            return False

        # Wait for description task
        time.sleep(2)

        # Then generate image
        response = requests.post(
            f"{BASE_URL}/projects/{self.project_id}/pages/{page_id}/generate/image",
            headers=headers,
            json={}
        )

        if response.status_code == 200:
            return True
        else:
            print_error(f"Failed to generate image: {response.text}")
            return False

    def test_quota_consumption(self):
        """Test quota consumption after image generation"""
        print_section("5. Testing Quota Consumption")

        # Get initial balance
        balance_before = self.get_quota_balance()
        print_info(f"Quota before generation: {balance_before} times")

        # Get first page
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{BASE_URL}/projects/{self.project_id}",
            headers=headers
        )

        if response.status_code != 200:
            print_error("Failed to get project")
            return False

        data = response.json()['data']
        pages = data.get('project', {}).get('pages') or data.get('pages', [])
        if not pages:
            print_error("No pages found")
            return False

        # Get page ID safely (API returns 'page_id' field)
        page_id = pages[0].get('page_id') or pages[0].get('id')
        if not page_id:
            print_error(f"Page has no ID. Page data: {pages[0]}")
            return False

        print_info(f"Generating image for page: {page_id}")

        # Generate image
        if not self.generate_single_image(page_id):
            return False

        # Wait for task to complete
        print_info("Waiting for generation to complete...")
        time.sleep(10)

        # Check quota after generation
        balance_after = self.get_quota_balance()
        print_info(f"Quota after generation: {balance_after} times")

        # Verify quota was consumed
        # Image generation costs 1 quota, description costs 0.1 (rounded to 1)
        expected_consumption = 1  # Only image generation should consume 1 quota
        actual_consumption = balance_before - balance_after

        if actual_consumption >= expected_consumption:
            print_success(f"Quota consumed correctly ({actual_consumption} times)")
            return True
        else:
            print_error(f"Expected to consume at least {expected_consumption}, but consumed {actual_consumption}")
            return False

    def test_insufficient_quota(self):
        """Test behavior when quota is insufficient"""
        print_section("6. Testing Insufficient Quota Handling")

        balance = self.get_quota_balance()
        print_info(f"Current quota: {balance} times")

        # Try to check for more quota than available
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{BASE_URL}/quota/check",
            headers=headers,
            json={
                "action": "generate_image",
                "required_quota": balance + 10  # Request more than available
            }
        )

        if response.status_code == 200:
            data = response.json()['data']
            if not data['sufficient']:
                print_success("Correctly detected insufficient quota")
                return True
            else:
                print_error("Should have detected insufficient quota")
                return False
        else:
            print_error(f"Quota check failed: {response.text}")
            return False

    def get_transaction_history(self):
        """Get quota transaction history"""
        print_section("7. Checking Transaction History")

        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{BASE_URL}/quota/transactions",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()['data']
            transactions = data['transactions']

            print_success(f"Found {len(transactions)} transactions")

            for tx in transactions:
                action = tx['action']
                amount = tx['amount']
                timestamp = tx['created_at']
                print_info(f"  - {action}: {amount} quota at {timestamp}")

            return True
        else:
            print_error(f"Failed to get transactions: {response.text}")
            return False

    def run_all_tests(self):
        """Run all commercial feature tests"""
        print("\n" + "="*60)
        print(" 🍌 Banana Slides - Commercial Features E2E Test")
        print("="*60)

        tests = [
            ("User Registration", self.register),
            ("Create Project", self.create_project),
            ("Generate Outline", self.generate_outline),
            ("Quota Check", self.test_quota_check),
            ("Quota Consumption", self.test_quota_consumption),
            ("Insufficient Quota", self.test_insufficient_quota),
            ("Transaction History", self.get_transaction_history),
        ]

        results = []

        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))

                if not result:
                    print_error(f"Test '{test_name}' failed, stopping...")
                    break

            except Exception as e:
                print_error(f"Test '{test_name}' crashed: {str(e)}")
                results.append((test_name, False))
                break

        # Print summary
        print_section("Test Summary")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        print(f"\nTests Passed: {passed}/{total}\n")

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")

        print("\n" + "="*60)

        return passed == total

if __name__ == "__main__":
    tester = CommercialTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
