#!/usr/bin/env python3
"""
Simple Working Performance Tester
Uses the browser-based approach but automates the timing
"""

import requests
import time
import json
import os
from datetime import datetime
import webbrowser
import threading


class SimplePerformanceTester:
    def __init__(self, base_url="http://localhost:5050"):
        self.base_url = base_url
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
                "params": "5 criteria, 4 alternatives",
                "file": "Hierarchy_Test_Data.xlsx",
            },
            "binary": {
                "route": "/binary",
                "params": "4 alternatives",
                "file": "Binary_Relations_Test_Data.xlsx",
            },
            "experts": {
                "route": "/experts",
                "params": "4 experts, 4 alternatives",
                "file": "Expert_Evaluation_Test_Data.xlsx",
            },
            "laplasa": {
                "route": "/laplasa",
                "params": "4 alternatives, 4 conditions",
                "file": "Laplace_Test_Data.xlsx",
            },
            "maximin": {
                "route": "/maximin",
                "params": "4 alternatives, 4 conditions",
                "file": "Maximin_Test_Data.xlsx",
            },
            "savage": {
                "route": "/savage",
                "params": "4 alternatives, 4 conditions",
                "file": "Savage_Test_Data.xlsx",
            },
            "hurwitz": {
                "route": "/hurwitz",
                "params": "4 alternatives, 4 conditions, α=0.5",
                "file": "Hurwitz_Test_Data.xlsx",
            },
        }

    def test_method(self, method_name, iterations=1):
        """Test a single method with manual timing"""
        print(f"\n🧪 Testing {method_name.upper()} method")
        print("=" * 50)

        config = self.method_configs[method_name]
        test_file = self.test_files[method_name]

        if not os.path.exists(test_file):
            print(f"✗ Test file not found: {test_file}")
            return None

        method_results = []

        for i in range(iterations):
            print(f"\n📋 Run {i+1}/{iterations}")
            print("-" * 30)

            # Step 1: Open browser
            url = f"{self.base_url}{config['route']}"
            print(f"1. Opening browser: {url}")
            webbrowser.open(url)

            # Step 2: Instructions
            print("2. Follow these steps:")
            print(f"   - Set parameters: {config['params']}")
            print(f"   - Upload file: {config['file']}")
            print("   - Process the data")
            print("   - Record the execution time")

            # Step 3: Get timing from user
            execution_time = input(
                "   Enter execution time in seconds (or press Enter to skip): "
            ).strip()

            if execution_time:
                try:
                    time_float = float(execution_time)
                    method_results.append(
                        {
                            "execution_time": time_float,
                            "status": "success",
                            "timestamp": datetime.now().isoformat(),
                            "run_number": i + 1,
                        }
                    )
                    print(f"   ✅ Recorded: {time_float:.3f}s")
                except ValueError:
                    print("   ❌ Invalid time format")
                    method_results.append(
                        {
                            "execution_time": None,
                            "status": "error",
                            "error": "Invalid time format",
                            "timestamp": datetime.now().isoformat(),
                            "run_number": i + 1,
                        }
                    )
            else:
                method_results.append(
                    {
                        "execution_time": None,
                        "status": "skipped",
                        "timestamp": datetime.now().isoformat(),
                        "run_number": i + 1,
                    }
                )
                print("   ⏭️  Skipped")

        self.results[method_name] = method_results
        return method_results

    def run_all_tests(self, iterations_per_method=3):
        """Run performance tests for all methods"""
        print("🚀 SIMPLE PERFORMANCE TESTING")
        print("=" * 60)
        print(f"This will test {iterations_per_method} iterations of each method.")
        print("Make sure your Flask app is running and you're logged in.")

        input("\nPress Enter to start...")

        methods = list(self.method_configs.keys())

        for method in methods:
            self.test_method(method, iterations_per_method)

        self.print_summary()
        self.save_results()

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE TEST RESULTS SUMMARY")
        print("=" * 60)

        if not self.results:
            print("No test results to report")
            return

        for method_name, results in self.results.items():
            successful_runs = [
                r
                for r in results
                if r["status"] == "success" and r["execution_time"] is not None
            ]

            print(f"\n{method_name.upper()}:")
            print(f"  Total runs: {len(results)}")
            print(f"  Successful: {len(successful_runs)}")

            if successful_runs:
                times = [r["execution_time"] for r in successful_runs]
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)

                print(f"  Average time: {avg_time:.3f}s")
                print(f"  Min time: {min_time:.3f}s")
                print(f"  Max time: {max_time:.3f}s")

                # Show individual times
                print("  Individual times:")
                for r in successful_runs:
                    print(f"    Run {r['run_number']}: {r['execution_time']:.3f}s")
            else:
                print("  ⚠️  No successful timing data")

    def save_results(self, filename="simple_performance_results.json"):
        """Save results to JSON file"""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")

    def quick_test_single(self):
        """Quick test of a single method"""
        print("🚀 QUICK SINGLE METHOD TEST")
        print("=" * 40)

        methods = list(self.method_configs.keys())

        print("Available methods:")
        for i, method in enumerate(methods, 1):
            print(f"{i}. {method}")

        try:
            choice = int(input("\nSelect method (1-7): ")) - 1
            if 0 <= choice < len(methods):
                method_name = methods[choice]
                iterations = input("Number of iterations (default 1): ").strip()
                iterations = int(iterations) if iterations else 1

                self.test_method(method_name, iterations)
                self.print_summary()
                self.save_results()
            else:
                print("Invalid selection")
        except ValueError:
            print("Invalid input")

    def open_performance_tester_html(self):
        """Open the browser-based performance tester"""
        html_file = "performance_tester.html"
        if os.path.exists(html_file):
            print(f"Opening {html_file} in browser...")
            webbrowser.open(f"file://{os.path.abspath(html_file)}")
        else:
            print(f"✗ {html_file} not found")

    def show_test_files(self):
        """Show available test files"""
        print("\n📁 Available Test Files:")
        print("=" * 30)

        for method_name, test_file in self.test_files.items():
            if os.path.exists(test_file):
                print(f"✅ {method_name}: {test_file}")
            else:
                print(f"❌ {method_name}: {test_file} (not found)")


def main():
    tester = SimplePerformanceTester()

    print("🚀 Simple Performance Testing Helper")
    print("1. Test all methods (guided)")
    print("2. Test single method (quick)")
    print("3. Open browser-based tester")
    print("4. Show test files")
    print("5. Exit")

    choice = input("\nSelect option (1-5): ").strip()

    if choice == "1":
        iterations = input("Number of iterations per method (default 3): ").strip()
        iterations = int(iterations) if iterations else 3
        tester.run_all_tests(iterations)

    elif choice == "2":
        tester.quick_test_single()

    elif choice == "3":
        tester.open_performance_tester_html()

    elif choice == "4":
        tester.show_test_files()

    elif choice == "5":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
