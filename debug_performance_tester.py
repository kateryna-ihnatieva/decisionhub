#!/usr/bin/env python3
"""
Debug Performance Tester - Let's see what's actually happening
"""

import requests
import time
import json
import os
from datetime import datetime


class DebugPerformanceTester:
    def __init__(self, base_url="http://localhost:5050"):
        self.base_url = base_url
        self.session = None

    def login(self, email="test@example.com", password="test_password"):
        """Login to get session"""
        login_data = {"email": email, "psw": password}
        response = requests.post(f"{self.base_url}/login", data=login_data)
        if response.status_code == 200:
            self.session = requests.Session()
            self.session.cookies = response.cookies
            print("✓ Login successful")
            return True
        else:
            print(f"✗ Login failed: {response.status_code}")
            return False

    def debug_upload(self, method_name="hierarchy"):
        """Debug the upload process step by step"""
        if not self.session:
            print("✗ No active session. Please login first.")
            return

        test_file = f"test_files/{method_name.title()}_Test_Data.xlsx"

        if not os.path.exists(test_file):
            print(f"✗ Test file not found: {test_file}")
            return

        print(f"\n🔍 Debugging {method_name.upper()} upload process...")

        try:
            # Step 1: Navigate to method index page
            print("1. Accessing method index page...")
            response = self.session.get(f"{self.base_url}/{method_name}")
            print(f"   Status: {response.status_code}")
            print(f"   URL: {response.url}")

            # Step 2: Navigate to names page
            print("2. Accessing names page...")
            names_data = {
                "num_criteria": 5,
                "num_alternatives": 4,
                f"{method_name}_task": "Choose the best smartphone",
            }
            response = self.session.post(
                f"{self.base_url}/{method_name}/names", data=names_data
            )
            print(f"   Status: {response.status_code}")
            print(f"   URL: {response.url}")

            # Step 3: Navigate to matrix page
            print("3. Accessing matrix page...")
            if method_name == "hierarchy":
                matrix_url = f"{self.base_url}/{method_name}/matrix-krit"
            elif method_name in ["laplasa", "maximin", "savage", "hurwitz"]:
                matrix_url = f"{self.base_url}/{method_name}/cost_matrix"
            else:
                matrix_url = f"{self.base_url}/{method_name}/matrix"

            response = self.session.get(matrix_url)
            print(f"   Status: {response.status_code}")
            print(f"   URL: {response.url}")

            # Step 4: Try to upload file
            print("4. Uploading file...")
            with open(test_file, "rb") as f:
                files = {"file": f}
                upload_data = {
                    "method_type": method_name,
                    "expected_criteria": 5,
                    "expected_alternatives": 4,
                }

                response = self.session.post(
                    f"{self.base_url}/upload_file", files=files, data=upload_data
                )

            print(f"   Status: {response.status_code}")
            print(f"   URL: {response.url}")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"   Content-Length: {len(response.content)}")

            # Check if it's JSON
            try:
                json_data = response.json()
                print("   ✓ Valid JSON response:")
                print(f"   {json.dumps(json_data, indent=2)}")
            except json.JSONDecodeError:
                print("   ✗ Not JSON response")
                print("   First 500 characters of response:")
                print(f"   {response.text[:500]}")

                # Check if it's a redirect
                if response.status_code in [301, 302, 303, 307, 308]:
                    print(
                        f"   Redirect to: {response.headers.get('Location', 'Unknown')}"
                    )

        except Exception as e:
            print(f"✗ Error: {str(e)}")

    def debug_all_methods(self):
        """Debug upload for all methods"""
        methods = [
            "hierarchy",
            "binary",
            "experts",
            "laplasa",
            "maximin",
            "savage",
            "hurwitz",
        ]

        if not self.login():
            return

        for method in methods:
            self.debug_upload(method)
            print("\n" + "=" * 60)


def main():
    tester = DebugPerformanceTester()

    print("🔍 Debug Performance Tester")
    print("1. Debug single method")
    print("2. Debug all methods")
    print("3. Exit")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        methods = [
            "hierarchy",
            "binary",
            "experts",
            "laplasa",
            "maximin",
            "savage",
            "hurwitz",
        ]
        print("\nAvailable methods:")
        for i, method in enumerate(methods, 1):
            print(f"{i}. {method}")

        method_choice = input("Select method (1-7): ").strip()
        try:
            method_idx = int(method_choice) - 1
            if 0 <= method_idx < len(methods):
                method_name = methods[method_idx]
                tester.debug_upload(method_name)
            else:
                print("Invalid method selection")
        except ValueError:
            print("Invalid input")

    elif choice == "2":
        tester.debug_all_methods()

    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
