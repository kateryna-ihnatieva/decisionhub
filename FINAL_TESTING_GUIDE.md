# Decision Methods Testing Suite

This directory contains test files and scripts for evaluating and comparing different decision-making methods implemented in the Decision Hub system.

## 📁 Test Files Created

All test files use the same scenario: **Choosing the best smartphone** with 4 alternatives and consistent data structure for fair comparison.

### Test Files:
1. **Hierarchy_Test_Data.xlsx** - Analytic Hierarchy Process (AHP)
2. **Binary_Relations_Test_Data.xlsx** - Binary Relations Analysis
3. **Expert_Evaluation_Test_Data.xlsx** - Expert Evaluation Method
4. **Laplace_Test_Data.xlsx** - Laplace Criterion
5. **Maximin_Test_Data.xlsx** - Maximin Criterion
6. **Savage_Test_Data.xlsx** - Savage Criterion (Minimax Regret)
7. **Hurwitz_Test_Data.xlsx** - Hurwitz Criterion

## 🎯 Test Scenario

**Decision**: Choose the best smartphone

**Alternatives**:
- iPhone 15
- Samsung Galaxy S24
- Google Pixel 8
- OnePlus 12

**Criteria** (for AHP and Expert methods):
- Price
- Camera Quality
- Battery Life
- Performance
- Design

**Conditions** (for uncertainty methods):
- Economic Growth
- Stable Economy
- Economic Decline
- Market Volatility

## 🚀 Quick Start

1. **Start your Flask application**:
   ```bash
   python app.py
   ```

2. **Choose your testing method**:

   **Option A: Browser-based testing (Recommended)**
   - Open `performance_tester.html` in your browser
   - Use the built-in timer and result tracking

   **Option B: Manual guided testing**
   ```bash
   python manual_performance_tester.py
   ```

   **Option C: Automated testing (Advanced)**
   ```bash
   python improved_performance_tester.py
   ```

## 🧪 Testing Methods

### Method 1: Browser-Based Testing (Easiest)

1. **Open** `performance_tester.html` in your browser
2. **Login** to your account at http://localhost:5050
3. **Test each method**:
   - Navigate to the method page
   - Set parameters (use the values below)
   - Upload the corresponding test file
   - Record execution time using the built-in timer
4. **Export results** as JSON when done

### Method 2: Manual Guided Testing

1. **Run the guided tester**:
   ```bash
   python manual_performance_tester.py
   ```
2. **Follow the step-by-step instructions**
3. **Record timing** using browser dev tools or manual timing
4. **Results are automatically saved** to JSON file

### Method 3: Automated Testing (Advanced)

1. **Create test user** (if needed):
   - Go to http://localhost:5050/register
   - Create account with email: test@example.com, password: test_password
2. **Run automated tester**:
   ```bash
   python improved_performance_tester.py
   ```
3. **Choose testing option** and let it run automatically

## 📋 Test Parameters

For each method, use these parameters:

### Hierarchy (AHP)
- **Route**: `/hierarchy`
- **Parameters**: 5 criteria, 4 alternatives
- **File**: `Hierarchy_Test_Data.xlsx`

### Binary Relations
- **Route**: `/binary`
- **Parameters**: 4 alternatives
- **File**: `Binary_Relations_Test_Data.xlsx`

### Expert Evaluation
- **Route**: `/experts`
- **Parameters**: 4 experts, 4 alternatives
- **File**: `Expert_Evaluation_Test_Data.xlsx`

### Laplace Criterion
- **Route**: `/laplasa`
- **Parameters**: 4 alternatives, 4 conditions
- **File**: `Laplace_Test_Data.xlsx`

### Maximin Criterion
- **Route**: `/maximin`
- **Parameters**: 4 alternatives, 4 conditions
- **File**: `Maximin_Test_Data.xlsx`

### Savage Criterion
- **Route**: `/savage`
- **Parameters**: 4 alternatives, 4 conditions
- **File**: `Savage_Test_Data.xlsx`

### Hurwitz Criterion
- **Route**: `/hurwitz`
- **Parameters**: 4 alternatives, 4 conditions, α=0.5
- **File**: `Hurwitz_Test_Data.xlsx`

## 📊 What to Measure

For each method, record:

1. **Execution Time**: How long it takes to process the data
2. **Optimal Alternative**: Which alternative is recommended
3. **Ranking**: Order of all alternatives
4. **Consistency**: Are results logical and reasonable?
5. **Usability**: How easy is it to use the method?

## 🔍 Comparison Criteria

Compare methods on:

- **Speed**: Which method is fastest?
- **Accuracy**: Which gives the best recommendations?
- **Consistency**: Which is most reliable?
- **Usability**: Which is easiest to use?
- **Robustness**: Which handles data variations best?

## 📈 Expected Results

Based on the test scenario, you should see:

- **Consistent alternatives** across all methods
- **Different rankings** depending on method philosophy
- **Varying execution times** based on complexity
- **Logical recommendations** for smartphone selection

## 🛠️ Troubleshooting

### Common Issues:

1. **Login problems**: Make sure you're logged in to your account
2. **File upload errors**: Check that test files exist in `test_files/` directory
3. **Parameter errors**: Use the exact parameters listed above
4. **Timing issues**: Use browser dev tools Network tab for accurate timing

### Getting Help:

- Check browser console for JavaScript errors
- Check Flask app logs for server errors
- Verify all test files are present and readable
- Ensure Flask app is running on correct port (5050)

## 📁 Files in This Suite

- `test_files/` - Directory containing all Excel test files
- `performance_tester.html` - Browser-based testing interface
- `manual_performance_tester.py` - Guided manual testing script
- `improved_performance_tester.py` - Advanced automated testing
- `create_test_files.py` - Script that generated the test files
- `TESTING_README.md` - This file
- `MANUAL_TESTING_GUIDE.md` - Detailed manual testing instructions
- `TESTING_SUITE_SUMMARY.md` - Overview of all testing tools

## 🎯 Next Steps

1. **Choose your preferred testing method**
2. **Run tests** for all 7 decision methods
3. **Record results** systematically
4. **Compare methods** on speed, accuracy, and usability
5. **Document findings** for your thesis

Good luck with your testing! 🚀
