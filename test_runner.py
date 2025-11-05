#!/usr/bin/env python3
"""
Simple Test Runner for Decision Methods
This script provides easy commands to test different decision-making methods
"""

import os
import sys
import time
from datetime import datetime


def print_header():
    print("=" * 70)
    print("DECISION METHODS TESTING SUITE")
    print("=" * 70)
    print("Test files created for comparing decision-making methods")
    print("All methods use the same scenario: Choosing the best smartphone")
    print(
        "with 4 alternatives: iPhone 15, Samsung Galaxy S24, Google Pixel 8, OnePlus 12"
    )
    print()


def list_test_files():
    print("AVAILABLE TEST FILES:")
    print("-" * 40)

    test_files = [
        ("Hierarchy_Test_Data.xlsx", "Analytic Hierarchy Process (AHP)"),
        ("Binary_Relations_Test_Data.xlsx", "Binary Relations Analysis"),
        ("Expert_Evaluation_Test_Data.xlsx", "Expert Evaluation Method"),
        ("Laplace_Test_Data.xlsx", "Laplace Criterion"),
        ("Maximin_Test_Data.xlsx", "Maximin Criterion"),
        ("Savage_Test_Data.xlsx", "Savage Criterion (Minimax Regret)"),
        ("Hurwitz_Test_Data.xlsx", "Hurwitz Criterion"),
    ]

    for i, (filename, description) in enumerate(test_files, 1):
        file_path = f"test_files/{filename}"
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"{i:2d}. {filename:<35} - {description}")
            print(f"    Size: {size:,} bytes")
        else:
            print(f"{i:2d}. {filename:<35} - FILE NOT FOUND")
        print()


def show_test_scenario():
    print("TEST SCENARIO:")
    print("-" * 20)
    print("Decision: Choose the best smartphone")
    print()
    print("Alternatives:")
    print("  1. iPhone 15")
    print("  2. Samsung Galaxy S24")
    print("  3. Google Pixel 8")
    print("  4. OnePlus 12")
    print()
    print("Criteria (for AHP and Expert methods):")
    print("  1. Price")
    print("  2. Camera Quality")
    print("  3. Battery Life")
    print("  4. Performance")
    print("  5. Design")
    print()
    print("Market Conditions (for Decision methods):")
    print("  1. High Demand")
    print("  2. Medium Demand")
    print("  3. Low Demand")
    print("  4. Economic Crisis")
    print()


def show_testing_instructions():
    print("HOW TO TEST:")
    print("-" * 20)
    print("1. Start your Flask application:")
    print("   python app.py")
    print()
    print("2. Open your browser and go to:")
    print("   http://localhost:5000")
    print()
    print("3. Login to your account")
    print()
    print("4. For each method:")
    print("   a) Go to the method's page")
    print("   b) Click 'Upload File' button")
    print("   c) Select the corresponding test file")
    print("   d) Fill in the required parameters")
    print("   e) Click 'Process File'")
    print("   f) Record the results and execution time")
    print()
    print("5. Compare results:")
    print("   - Which method gives the best recommendation?")
    print("   - Which method is fastest?")
    print("   - Which method is most consistent?")
    print()


def show_performance_testing():
    print("PERFORMANCE TESTING:")
    print("-" * 25)
    print("Use the performance_tester.py script for automated testing:")
    print()
    print("1. Make sure your Flask app is running")
    print("2. Run the performance tester:")
    print("   python performance_tester.py")
    print()
    print("3. Choose option 1 for comprehensive testing")
    print("4. The script will:")
    print("   - Test each method multiple times")
    print("   - Measure execution times")
    print("   - Generate a performance report")
    print("   - Save results to JSON file")
    print()


def show_expected_results():
    print("EXPECTED RESULTS COMPARISON:")
    print("-" * 35)
    print("All methods should ideally recommend the same optimal alternative")
    print("if the data is consistent and the methods are properly implemented.")
    print()
    print("However, different methods may give different results because:")
    print("- They use different mathematical approaches")
    print("- They handle uncertainty differently")
    print("- They weight criteria differently")
    print()
    print("This is normal and expected in decision analysis!")
    print()


def main():
    print_header()

    while True:
        print("\nOPTIONS:")
        print("1. List test files")
        print("2. Show test scenario")
        print("3. Show testing instructions")
        print("4. Show performance testing info")
        print("5. Show expected results")
        print("6. Exit")

        choice = input("\nSelect option (1-6): ").strip()

        if choice == "1":
            list_test_files()
        elif choice == "2":
            show_test_scenario()
        elif choice == "3":
            show_testing_instructions()
        elif choice == "4":
            show_performance_testing()
        elif choice == "5":
            show_expected_results()
        elif choice == "6":
            print("\nGoodbye! Happy testing!")
            break
        else:
            print("Invalid choice. Please select 1-6.")


if __name__ == "__main__":
    main()
