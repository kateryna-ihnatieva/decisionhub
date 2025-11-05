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

**Market Conditions** (for Decision methods):
- High Demand
- Medium Demand
- Low Demand
- Economic Crisis

## 🚀 How to Test

### Manual Testing:
1. Start your Flask application: `python app.py`
2. Open browser: `http://localhost:5000`
3. Login to your account
4. For each method:
   - Go to the method's page
   - Click 'Upload File' button
   - Select the corresponding test file
   - Fill in required parameters
   - Click 'Process File'
   - Record results and execution time

### Automated Performance Testing:
1. Make sure Flask app is running
2. Run: `python performance_tester.py`
3. Choose option 1 for comprehensive testing
4. The script will test each method multiple times and generate a performance report

## 📊 What to Compare

### Performance Metrics:
- **Execution Time**: How fast each method processes the data
- **Memory Usage**: Resource consumption during processing
- **Success Rate**: Percentage of successful runs

### Result Quality:
- **Consistency**: Do results make logical sense?
- **Optimal Alternative**: Which smartphone is recommended?
- **Ranking**: How are alternatives ranked?
- **Confidence**: How certain is the recommendation?

### Method Characteristics:
- **Complexity**: How complex is the input data required?
- **User Experience**: How easy is it to use?
- **Interpretability**: How easy are results to understand?

## 🔧 Testing Scripts

### `create_test_files.py`
Creates all test Excel files with consistent data structure.

### `performance_tester.py`
Automated performance testing script that:
- Tests each method multiple times
- Measures execution times
- Generates performance reports
- Saves results to JSON files

### `test_runner.py`
Interactive script providing:
- Test file information
- Testing instructions
- Performance testing guidance
- Expected results explanation

## 📈 Expected Results

All methods should ideally recommend the same optimal alternative if the data is consistent. However, different methods may give different results because:

- They use different mathematical approaches
- They handle uncertainty differently
- They weight criteria differently

**This is normal and expected in decision analysis!**

## 🎯 Testing Goals

1. **Performance Comparison**: Which method is fastest?
2. **Result Quality**: Which method gives the best recommendations?
3. **Consistency**: Which method is most reliable?
4. **Usability**: Which method is easiest to use?
5. **Robustness**: Which method handles edge cases best?

## 📝 Recording Results

Create a comparison table:

| Method | Execution Time | Optimal Alternative | Ranking | Notes |
|--------|---------------|-------------------|---------|-------|
| AHP | X.XXs | iPhone 15 | 1. iPhone, 2. Samsung, ... | Most comprehensive |
| Binary | X.XXs | Samsung Galaxy | 1. Samsung, 2. iPhone, ... | Simple but effective |
| Experts | X.XXs | Google Pixel | 1. Pixel, 2. OnePlus, ... | Uses expert knowledge |
| Laplace | X.XXs | iPhone 15 | 1. iPhone, 2. Samsung, ... | Equal probability |
| Maximin | X.XXs | OnePlus 12 | 1. OnePlus, 2. Pixel, ... | Conservative approach |
| Savage | X.XXs | Samsung Galaxy | 1. Samsung, 2. iPhone, ... | Minimizes regret |
| Hurwitz | X.XXs | iPhone 15 | 1. iPhone, 2. Samsung, ... | Balanced optimism |

## 🔍 Analysis Questions

1. **Which method is fastest?** (Performance)
2. **Which method gives the most logical result?** (Quality)
3. **Which method is most consistent across runs?** (Reliability)
4. **Which method is easiest to understand?** (Usability)
5. **Which method handles uncertainty best?** (Robustness)

## 📋 Next Steps

After testing:
1. Analyze the results
2. Identify the best performing method
3. Document findings
4. Consider improvements
5. Update system recommendations

---

**Happy Testing!** 🚀
