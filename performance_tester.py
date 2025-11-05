import time
import requests
import os
from datetime import datetime
import json


class DecisionMethodPerformanceTester:
    def __init__(self, base_url="http://localhost:5050"):
        self.base_url = base_url
        self.results = {}
        self.test_files = {
            "hierarchy": "test_files/Hierarchy_Test_Data.xlsx",
            "binary": "test_files/Binary_Relations_Test_Data.xlsx",
            "experts": "test_files/Expert_Evaluation_Test_Data.xlsx",
            "laplace": "test_files/Laplace_Test_Data.xlsx",
            "maximin": "test_files/Maximin_Test_Data.xlsx",
            "savage": "test_files/Savage_Test_Data.xlsx",
            "hurwitz": "test_files/Hurwitz_Test_Data.xlsx",
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
            print("✗ Login failed")
            return False

    def test_method_performance(self, method_name, test_file_path, iterations=5):
        """Test performance of a specific decision method"""
        print(f"\nTesting {method_name.upper()} method...")

        if not os.path.exists(test_file_path):
            print(f"✗ Test file not found: {test_file_path}")
            return None

        times = []
        successful_runs = 0

        for i in range(iterations):
            print(f"  Run {i+1}/{iterations}...", end=" ")

            start_time = time.time()

            try:
                # Upload file
                with open(test_file_path, "rb") as f:
                    files = {"file": f}
                    data = {
                        "method_type": method_name,
                        "expected_criteria": (
                            5 if method_name in ["hierarchy", "experts"] else 4
                        ),
                        "expected_alternatives": 4,
                    }

                    response = self.session.post(
                        f"{self.base_url}/upload_file", files=files, data=data
                    )

                if response.status_code == 200:
                    upload_data = response.json()
                    if upload_data.get("success"):
                        # Process the uploaded data
                        process_data = {
                            "uploaded_alternatives_names": json.dumps(
                                upload_data.get("alternative_names", [])
                            ),
                            "uploaded_conditions_names": json.dumps(
                                upload_data.get("condition_names", [])
                            ),
                            "uploaded_cost_matrix": json.dumps(
                                upload_data.get("matrix", [])
                            ),
                            "matrix_type": "cost",
                        }

                        # Add method-specific parameters
                        if method_name == "hurwitz":
                            process_data["alpha"] = 0.5

                        # Submit for processing
                        process_response = self.session.post(
                            f"{self.base_url}/{method_name}/result_from_file",
                            data=process_data,
                        )

                        if process_response.status_code == 200:
                            end_time = time.time()
                            execution_time = end_time - start_time
                            times.append(execution_time)
                            successful_runs += 1
                            print(f"✓ {execution_time:.3f}s")
                        else:
                            print("✗ Processing failed")
                    else:
                        print("✗ Upload failed")
                else:
                    print("✗ Upload request failed")

            except Exception as e:
                print(f"✗ Error: {str(e)}")

            # Small delay between runs
            time.sleep(0.5)

        if successful_runs > 0:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            result = {
                "method": method_name,
                "successful_runs": successful_runs,
                "total_runs": iterations,
                "avg_time": avg_time,
                "min_time": min_time,
                "max_time": max_time,
                "times": times,
            }

            print(
                f"  Results: Avg={avg_time:.3f}s, Min={min_time:.3f}s, Max={max_time:.3f}s"
            )
            return result
        else:
            print(f"  ✗ No successful runs for {method_name}")
            return None

    def run_all_tests(self, iterations=5):
        """Run performance tests for all methods"""
        print("=" * 60)
        print("DECISION METHOD PERFORMANCE TESTING")
        print("=" * 60)
        print(f"Testing {iterations} iterations per method")
        print(f"Base URL: {self.base_url}")

        if not self.login():
            print("Cannot proceed without login")
            return

        all_results = []

        # Test each method
        for method, file_path in self.test_files.items():
            result = self.test_method_performance(method, file_path, iterations)
            if result:
                all_results.append(result)

        # Generate report
        self.generate_report(all_results)

    def generate_report(self, results):
        """Generate performance comparison report"""
        print("\n" + "=" * 60)
        print("PERFORMANCE TEST RESULTS")
        print("=" * 60)

        if not results:
            print("No successful test results to report")
            return

        # Sort by average execution time
        results.sort(key=lambda x: x["avg_time"])

        print(
            f"{'Method':<15} {'Avg Time':<10} {'Min Time':<10} {'Max Time':<10} {'Success Rate':<12}"
        )
        print("-" * 70)

        for result in results:
            success_rate = (result["successful_runs"] / result["total_runs"]) * 100
            print(
                f"{result['method']:<15} {result['avg_time']:<10.3f} {result['min_time']:<10.3f} {result['max_time']:<10.3f} {success_rate:<12.1f}%"
            )

        # Find fastest and slowest
        fastest = results[0]
        slowest = results[-1]

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Fastest Method: {fastest['method']} ({fastest['avg_time']:.3f}s)")
        print(f"Slowest Method: {slowest['method']} ({slowest['avg_time']:.3f}s)")
        print(f"Speed Difference: {slowest['avg_time']/fastest['avg_time']:.2f}x")

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"performance_test_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(
                {
                    "timestamp": timestamp,
                    "test_results": results,
                    "summary": {
                        "fastest_method": fastest["method"],
                        "slowest_method": slowest["method"],
                        "speed_ratio": slowest["avg_time"] / fastest["avg_time"],
                    },
                },
                f,
                indent=2,
            )

        print(f"\nDetailed report saved to: {report_file}")

    def test_single_method(self, method_name, iterations=10):
        """Test a single method with more iterations for detailed analysis"""
        if method_name not in self.test_files:
            print(f"Unknown method: {method_name}")
            return

        if not self.login():
            return

        file_path = self.test_files[method_name]
        result = self.test_method_performance(method_name, file_path, iterations)

        if result:
            print(f"\nDetailed Analysis for {method_name.upper()}:")
            print(
                f"  Successful runs: {result['successful_runs']}/{result['total_runs']}"
            )
            print(f"  Average time: {result['avg_time']:.3f}s")
            print(f"  Min time: {result['min_time']:.3f}s")
            print(f"  Max time: {result['max_time']:.3f}s")
            print(f"  All times: {[f'{t:.3f}s' for t in result['times']]}")


def main():
    """Main function to run performance tests"""
    tester = DecisionMethodPerformanceTester()

    print("Decision Method Performance Tester")
    print("1. Run all methods (5 iterations each)")
    print("2. Test single method (10 iterations)")
    print("3. Exit")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        iterations = int(input("Number of iterations per method (default 5): ") or "5")
        tester.run_all_tests(iterations)
    elif choice == "2":
        method = input(
            "Method name (hierarchy/binary/experts/laplace/maximin/savage/hurwitz): "
        ).strip()
        iterations = int(input("Number of iterations (default 10): ") or "10")
        tester.test_single_method(method, iterations)
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
