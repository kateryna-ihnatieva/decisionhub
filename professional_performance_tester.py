#!/usr/bin/env python3
"""
Professional Automated Performance Tester for Decision Methods
Follows the exact workflow: index -> names -> matrix -> result
"""

import requests
import time
import json
import os
from datetime import datetime
from urllib.parse import urljoin


class ProfessionalPerformanceTester:
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

        # Method configurations with exact workflow
        self.method_configs = {
            "hierarchy": {
                "index_route": "/hierarchy",
                "names_route": "/hierarchy/names",
                "matrix_route": "/hierarchy/matrix-krit",
                "result_route": "/hierarchy/result",
                "upload_route": "/hierarchy/upload_matrix",
                "result_from_file_route": "/hierarchy/result_from_file",
                "params": {
                    "num_criteria": 5,
                    "num_alternatives": 4,
                    "hierarchy_task": "Choose the best smartphone",
                },
            },
            "binary": {
                "index_route": "/binary",
                "names_route": "/binary/names",
                "matrix_route": "/binary/matrix",
                "result_route": "/binary/result",
                "upload_route": "/binary/upload_matrix",
                "result_from_file_route": "/binary/result_from_file",
                "params": {
                    "num_alternatives": 4,
                    "binary_task": "Choose the best smartphone",
                },
            },
            "experts": {
                "index_route": "/experts",
                "names_route": "/experts/names",
                "matrix_route": "/experts/experts_data",
                "result_route": "/experts/result",
                "upload_route": "/experts/upload_matrix",
                "result_from_file_route": "/experts/result_from_file",
                "params": {
                    "num_experts": 4,
                    "num_alternatives": 4,
                    "experts_task": "Choose the best smartphone",
                },
            },
            "laplasa": {
                "index_route": "/laplasa",
                "names_route": "/laplasa/names",
                "matrix_route": "/laplasa/cost_matrix",
                "result_route": "/laplasa/result",
                "upload_route": "/laplasa/upload_matrix",
                "result_from_file_route": "/laplasa/result_from_file",
                "params": {
                    "num_alt": 4,
                    "num_conditions": 4,
                    "laplasa_task": "Choose the best smartphone",
                },
            },
            "maximin": {
                "index_route": "/maximin",
                "names_route": "/maximin/names",
                "matrix_route": "/maximin/cost_matrix",
                "result_route": "/maximin/result",
                "upload_route": "/maximin/upload_matrix",
                "result_from_file_route": "/maximin/result_from_file",
                "params": {
                    "num_alt": 4,
                    "num_conditions": 4,
                    "maximin_task": "Choose the best smartphone",
                },
            },
            "savage": {
                "index_route": "/savage",
                "names_route": "/savage/names",
                "matrix_route": "/savage/cost_matrix",
                "result_route": "/savage/result",
                "upload_route": "/savage/upload_matrix",
                "result_from_file_route": "/savage/result_from_file",
                "params": {
                    "num_alt": 4,
                    "num_conditions": 4,
                    "savage_task": "Choose the best smartphone",
                },
            },
            "hurwitz": {
                "index_route": "/hurwitz",
                "names_route": "/hurwitz/names",
                "matrix_route": "/hurwitz/cost_matrix",
                "result_route": "/hurwitz/result",
                "upload_route": "/hurwitz/upload_matrix",
                "result_from_file_route": "/hurwitz/result_from_file",
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
        """Test a single method following the exact workflow"""
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

                # Step 1: Navigate to method index page
                response = self.session.get(f"{self.base_url}{config['index_route']}")
                if response.status_code != 200:
                    print(f"✗ Failed to access index: {response.status_code}")
                    continue

                # Step 2: Navigate to names page and set parameters
                names_data = config["params"].copy()
                response = self.session.post(
                    f"{self.base_url}{config['names_route']}", data=names_data
                )
                if response.status_code not in [200, 302]:
                    print(f"✗ Failed to set parameters: {response.status_code}")
                    continue

                # Step 3: Navigate to matrix page (this sets up the session)
                response = self.session.get(f"{self.base_url}{config['matrix_route']}")
                if response.status_code != 200:
                    print(f"✗ Failed to access matrix page: {response.status_code}")
                    continue

                # Step 4: Upload file using the method-specific upload route
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

                # Step 5: Process the uploaded data using result_from_file
                process_data = {**config["params"], **upload_result.get("data", {})}

                # For hierarchy, we need to handle the special case
                if method_name == "hierarchy":
                    # Hierarchy uses different field names
                    process_data.update(
                        {
                            "criteria_names": json.dumps(
                                upload_result.get("data", {}).get("criteria_names", [])
                            ),
                            "alternatives_names": json.dumps(
                                upload_result.get("data", {}).get(
                                    "alternative_names", []
                                )
                            ),
                            "criteria_matrix": json.dumps(
                                upload_result.get("data", {}).get("matrices", [])[0]
                                if upload_result.get("data", {}).get("matrices")
                                else []
                            ),
                            "alternatives_matrices": json.dumps(
                                upload_result.get("data", {}).get("matrices", [])[1:]
                                if len(
                                    upload_result.get("data", {}).get("matrices", [])
                                )
                                > 1
                                else []
                            ),
                        }
                    )
                elif method_name == "experts":
                    # Experts uses different field names
                    process_data.update(
                        {
                            "competency_matrix": json.dumps(
                                upload_result.get("data", {}).get("matrices", [])[0]
                                if upload_result.get("data", {}).get("matrices")
                                else []
                            ),
                            "evaluation_matrix": json.dumps(
                                upload_result.get("data", {}).get("matrices", [])[1]
                                if len(
                                    upload_result.get("data", {}).get("matrices", [])
                                )
                                > 1
                                else []
                            ),
                            "alternatives_names": json.dumps(
                                upload_result.get("data", {}).get(
                                    "alternative_names", []
                                )
                            ),
                        }
                    )
                elif method_name == "binary":
                    # Binary uses different field names
                    process_data.update(
                        {
                            "names": json.dumps(
                                upload_result.get("data", {}).get(
                                    "alternative_names", []
                                )
                            ),
                            "matrix": json.dumps(
                                upload_result.get("data", {}).get("matrix", [])
                            ),
                        }
                    )
                else:
                    # Other methods (laplasa, maximin, savage, hurwitz)
                    process_data.update(
                        {
                            "alternatives_names": json.dumps(
                                upload_result.get("data", {}).get(
                                    "alternative_names", []
                                )
                            ),
                            "conditions_names": json.dumps(
                                upload_result.get("data", {}).get("condition_names", [])
                            ),
                            "cost_matrix": json.dumps(
                                upload_result.get("data", {}).get("matrix", [])
                            ),
                        }
                    )

                response = self.session.post(
                    f"{self.base_url}{config['result_from_file_route']}",
                    data=process_data,
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
        print("🚀 PROFESSIONAL DECISION METHOD PERFORMANCE TESTING")
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

    def save_results(self, filename="professional_performance_results.json"):
        """Save results to JSON file"""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")

    def test_single_method(self, method_name, iterations=10):
        """Test a single method with detailed output"""
        print(f"\n🎯 Testing {method_name.upper()} method only")
        print("=" * 50)

        if not self.login():
            return

        results = self.test_method(method_name, iterations)
        if results:
            self.results[method_name] = results
            self.print_summary()
            self.save_results(f"{method_name}_performance_results.json")


def main():
    tester = ProfessionalPerformanceTester()

    print("🚀 Professional Decision Method Performance Tester")
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

                tester.test_single_method(method_name, iterations)
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
