#!/usr/bin/env python3
"""
Improved Performance Tester for Decision Methods
Follows the proper workflow: navigate to method page -> set parameters -> upload file -> get results
"""

import requests
import time
import json
import os
from datetime import datetime


class ImprovedPerformanceTester:
    def __init__(self, base_url="http://localhost:5050"):
        self.base_url = base_url
        self.session = None
        self.results = {}

        # Test file paths
        self.test_files = {
            "hierarchy": "test_files/Hierarchy_Test_Data.xlsx",
            "binary": "test_files/Binary_Relations_Test_Data.xlsx",
            "experts": "test_files/Expert_Evaluation_Test_Data.xlsx",
            "laplasa": "test_files/Laplace_Test_Data.xlsx",
            "maximin": "test_files/Maximin_Test_Data.xlsx",
            "savage": "test_files/Savage_Test_Data.xlsx",
            "hurwitz": "test_files/Hurwitz_Test_Data.xlsx",
        }

        # Method configurations
        self.method_configs = {
            "hierarchy": {
                "route": "/hierarchy",
                "names_route": "/hierarchy/names",
                "matrix_route": "/hierarchy/matrix-krit",
                "result_route": "/hierarchy/result",
                "params": {
                    "num_criteria": 5,
                    "num_alternatives": 4,
                    "hierarchy_task": "Choose the best smartphone",
                },
            },
            "binary": {
                "route": "/binary",
                "names_route": "/binary/names",
                "matrix_route": "/binary/matrix",
                "result_route": "/binary/result",
                "params": {
                    "num_alternatives": 4,
                    "binary_task": "Choose the best smartphone",
                },
            },
            "experts": {
                "route": "/experts",
                "names_route": "/experts/names",
                "matrix_route": "/experts/experts_data",
                "result_route": "/experts/result",
                "params": {
                    "num_experts": 4,
                    "num_alternatives": 4,
                    "experts_task": "Choose the best smartphone",
                },
            },
            "laplasa": {
                "route": "/laplasa",
                "names_route": "/laplasa/names",
                "matrix_route": "/laplasa/cost_matrix",
                "result_route": "/laplasa/result",
                "params": {
                    "num_alt": 4,
                    "num_conditions": 4,
                    "laplasa_task": "Choose the best smartphone",
                },
            },
            "maximin": {
                "route": "/maximin",
                "names_route": "/maximin/names",
                "matrix_route": "/maximin/cost_matrix",
                "result_route": "/maximin/result",
                "params": {
                    "num_alt": 4,
                    "num_conditions": 4,
                    "maximin_task": "Choose the best smartphone",
                },
            },
            "savage": {
                "route": "/savage",
                "names_route": "/savage/names",
                "matrix_route": "/savage/cost_matrix",
                "result_route": "/savage/result",
                "params": {
                    "num_alt": 4,
                    "num_conditions": 4,
                    "savage_task": "Choose the best smartphone",
                },
            },
            "hurwitz": {
                "route": "/hurwitz",
                "names_route": "/hurwitz/names",
                "matrix_route": "/hurwitz/cost_matrix",
                "result_route": "/hurwitz/result",
                "params": {
                    "num_alt": 4,
                    "num_conditions": 4,
                    "alpha": 0.5,
                    "hurwitz_task": "Choose the best smartphone",
                },
            },
        }

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

    def test_method(self, method_name, iterations=1):
        """Test a single method following the proper workflow"""
        if not self.session:
            print("✗ No active session. Please login first.")
            return None

        config = self.method_configs[method_name]
        test_file = self.test_files[method_name]

        if not os.path.exists(test_file):
            print(f"✗ Test file not found: {test_file}")
            return None

        print(f"\n🧪 Testing {method_name.upper()} method...")
        method_results = []

        for i in range(iterations):
            print(f"  Run {i+1}/{iterations}...", end=" ")

            try:
                start_time = time.time()

                # Step 1: Navigate to method page
                response = self.session.get(f"{self.base_url}{config['route']}")
                if response.status_code != 200:
                    print(f"✗ Failed to access method page: {response.status_code}")
                    continue

                # Step 2: Navigate to names page and set parameters
                names_data = config["params"].copy()
                response = self.session.post(
                    f"{self.base_url}{config['names_route']}", data=names_data
                )
                if response.status_code not in [200, 302]:
                    print(f"✗ Failed to set parameters: {response.status_code}")
                    continue

                # Step 3: Upload file
                with open(test_file, "rb") as f:
                    files = {"file": f}
                    upload_data = {
                        "method_type": method_name,
                        "expected_criteria": config["params"].get(
                            "num_criteria", config["params"].get("num_conditions", 0)
                        ),
                        "expected_alternatives": config["params"].get(
                            "num_alternatives", config["params"].get("num_alt", 0)
                        ),
                    }

                    response = self.session.post(
                        f"{self.base_url}/upload_file", files=files, data=upload_data
                    )

                if response.status_code != 200:
                    print(f"✗ File upload failed: {response.status_code}")
                    continue

                try:
                    upload_result = response.json()
                    if not upload_result.get("success"):
                        print(f"✗ Upload error: {upload_result.get('error')}")
                        continue
                except json.JSONDecodeError:
                    print(f"✗ Invalid JSON response from upload")
                    continue

                # Step 4: Process the uploaded data
                process_data = {**config["params"], **upload_result.get("data", {})}

                response = self.session.post(
                    f"{self.base_url}{config['result_route']}", data=process_data
                )
                if response.status_code not in [200, 302]:
                    print(f"✗ Processing failed: {response.status_code}")
                    continue

                end_time = time.time()
                execution_time = end_time - start_time

                method_results.append(
                    {
                        "execution_time": execution_time,
                        "status": "success",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                print(f"✓ {execution_time:.3f}s")

            except Exception as e:
                print(f"✗ Error: {str(e)}")
                method_results.append(
                    {
                        "execution_time": None,
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return method_results

    def run_all_tests(self, iterations_per_method=5):
        """Run performance tests for all methods"""
        print("=" * 60)
        print("🚀 IMPROVED DECISION METHOD PERFORMANCE TESTING")
        print("=" * 60)
        print(f"Testing {iterations_per_method} iterations per method")
        print(f"Base URL: {self.base_url}")

        if not self.login():
            print("Cannot proceed without login")
            return

        for method_name in self.method_configs.keys():
            results = self.test_method(method_name, iterations_per_method)
            if results:
                self.results[method_name] = results

        self.print_summary()

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE TEST RESULTS")
        print("=" * 60)

        if not self.results:
            print("No successful test results to report")
            return

        for method_name, results in self.results.items():
            successful_runs = [r for r in results if r["status"] == "success"]

            if successful_runs:
                times = [r["execution_time"] for r in successful_runs]
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)

                print(f"\n{method_name.upper()}:")
                print(f"  Successful runs: {len(successful_runs)}/{len(results)}")
                print(f"  Average time: {avg_time:.3f}s")
                print(f"  Min time: {min_time:.3f}s")
                print(f"  Max time: {max_time:.3f}s")
            else:
                print(f"\n{method_name.upper()}:")
                print(f"  ✗ No successful runs ({len(results)} failed)")

    def save_results(self, filename="performance_results.json"):
        """Save results to JSON file"""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")


def main():
    tester = ImprovedPerformanceTester()

    print("🚀 Improved Decision Method Performance Tester")
    print("1. Run all methods (5 iterations each)")
    print("2. Test single method (10 iterations)")
    print("3. Exit")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        iterations = input("Number of iterations per method (default 5): ").strip()
        iterations = int(iterations) if iterations else 5
        tester.run_all_tests(iterations)
        tester.save_results()

    elif choice == "2":
        print("\nAvailable methods:")
        methods = list(tester.method_configs.keys())
        for i, method in enumerate(methods, 1):
            print(f"{i}. {method}")

        method_choice = input("Select method (1-7): ").strip()
        try:
            method_idx = int(method_choice) - 1
            if 0 <= method_idx < len(methods):
                method_name = methods[method_idx]
                iterations = input("Number of iterations (default 10): ").strip()
                iterations = int(iterations) if iterations else 10

                if tester.login():
                    results = tester.test_method(method_name, iterations)
                    if results:
                        tester.results[method_name] = results
                        tester.print_summary()
                        tester.save_results()
            else:
                print("Invalid method selection")
        except ValueError:
            print("Invalid input")

    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
