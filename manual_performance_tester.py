#!/usr/bin/env python3
"""
Simple Performance Tester - Manual Testing Helper
This script helps you test performance manually by providing step-by-step instructions
and timing tools.
"""

import time
import json
import os
from datetime import datetime


class ManualPerformanceTester:
    def __init__(self):
        self.results = {}
        self.start_time = None

    def start_timer(self):
        """Start timing"""
        self.start_time = time.time()
        print("⏱️  Timer started!")

    def stop_timer(self):
        """Stop timing and return elapsed time"""
        if self.start_time is None:
            print("❌ Timer was not started!")
            return None

        elapsed = time.time() - self.start_time
        print(f"⏱️  Elapsed time: {elapsed:.3f} seconds")
        self.start_time = None
        return elapsed

    def test_method(self, method_name, iterations=1):
        """Guide user through testing a method"""
        print(f"\n🧪 Testing {method_name.upper()} method")
        print("=" * 50)

        method_results = []

        for i in range(iterations):
            print(f"\n📋 Run {i+1}/{iterations}")
            print("-" * 30)

            # Step 1: Navigate to method
            input(f"1. Open browser and go to: http://localhost:5050/{method_name}")
            input("   Press Enter when page is loaded...")

            # Step 2: Set parameters
            print("2. Set the following parameters:")
            if method_name == "hierarchy":
                print("   - Number of criteria: 5")
                print("   - Number of alternatives: 4")
                print("   - Task description: 'Choose the best smartphone'")
            elif method_name in ["laplasa", "maximin", "savage", "hurwitz"]:
                print("   - Number of alternatives: 4")
                print("   - Number of conditions: 4")
                print("   - Task description: 'Choose the best smartphone'")
                if method_name == "hurwitz":
                    print("   - Alpha coefficient: 0.5")
            elif method_name == "binary":
                print("   - Number of alternatives: 4")
                print("   - Task description: 'Choose the best smartphone'")
            elif method_name == "experts":
                print("   - Number of experts: 4")
                print("   - Number of alternatives: 4")
                print("   - Task description: 'Choose the best smartphone'")

            input("   Press Enter when parameters are set...")

            # Step 3: Upload file
            test_file = f"test_files/{method_name.title()}_Test_Data.xlsx"
            print(f"3. Upload file: {test_file}")
            input("   Press Enter when file is uploaded...")

            # Step 4: Process and get results
            print("4. Click 'Process' or 'Calculate' to get results")
            input("   Press Enter when processing is complete...")

            # Step 5: Record timing
            print("5. Record the execution time:")
            print("   - Use browser dev tools (F12 -> Network tab)")
            print("   - Or use the built-in timer in performance_tester.html")

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
        """Guide user through testing all methods"""
        print("🚀 MANUAL PERFORMANCE TESTING GUIDE")
        print("=" * 60)
        print(
            f"This will guide you through testing {iterations_per_method} iterations of each method."
        )
        print("Make sure your Flask app is running on http://localhost:5050")
        print("And that you have logged in to your account.")

        input("\nPress Enter to start...")

        methods = [
            "hierarchy",
            "binary",
            "experts",
            "laplasa",
            "maximin",
            "savage",
            "hurwitz",
        ]

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

    def save_results(self, filename="manual_performance_results.json"):
        """Save results to JSON file"""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")

    def quick_test_single(self):
        """Quick test of a single method"""
        print("🚀 QUICK SINGLE METHOD TEST")
        print("=" * 40)

        methods = [
            "hierarchy",
            "binary",
            "experts",
            "laplasa",
            "maximin",
            "savage",
            "hurwitz",
        ]

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


def main():
    tester = ManualPerformanceTester()

    print("🚀 Manual Performance Testing Helper")
    print("1. Test all methods (guided)")
    print("2. Test single method (quick)")
    print("3. Exit")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        iterations = input("Number of iterations per method (default 3): ").strip()
        iterations = int(iterations) if iterations else 3
        tester.run_all_tests(iterations)

    elif choice == "2":
        tester.quick_test_single()

    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
