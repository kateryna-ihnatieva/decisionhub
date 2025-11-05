# 🚀 Manual Performance Testing Guide

Since the automated performance tester needs database access, here's a manual approach to test and compare all decision methods:

## 📋 Testing Checklist

### 1. Prepare Your Environment
- [ ] Flask app is running on `http://localhost:5050`
- [ ] You have a user account (register if needed)
- [ ] Test files are created in `test_files/` directory

### 2. Test Each Method Manually

For each method, record:
- **Execution Time**: Use browser dev tools or stopwatch
- **Result**: Which alternative is recommended
- **Ranking**: Order of alternatives
- **Notes**: Any issues or observations

### 3. Test Files Mapping

| Method | Test File | Parameters Needed |
|--------|-----------|-------------------|
| **AHP** | `Hierarchy_Test_Data.xlsx` | 5 criteria, 4 alternatives |
| **Binary Relations** | `Binary_Relations_Test_Data.xlsx` | 4 alternatives |
| **Expert Evaluation** | `Expert_Evaluation_Test_Data.xlsx` | 4 experts, 4 alternatives |
| **Laplace** | `Laplace_Test_Data.xlsx` | 4 alternatives, 4 conditions |
| **Maximin** | `Maximin_Test_Data.xlsx` | 4 alternatives, 4 conditions |
| **Savage** | `Savage_Test_Data.xlsx` | 4 alternatives, 4 conditions |
| **Hurwitz** | `Hurwitz_Test_Data.xlsx` | 4 alternatives, 4 conditions, α=0.5 |

### 4. Testing Steps for Each Method

1. **Navigate** to the method's page
2. **Click** "Upload File" button
3. **Select** the corresponding test file
4. **Fill** in required parameters
5. **Start timer** before clicking "Process File"
6. **Stop timer** when results appear
7. **Record** the results and time

### 5. Results Recording Template

```
Method: [Method Name]
Execution Time: [X.XX seconds]
Optimal Alternative: [Alternative Name]
Ranking:
1. [Alternative] - [Score/Value]
2. [Alternative] - [Score/Value]
3. [Alternative] - [Score/Value]
4. [Alternative] - [Score/Value]
Notes: [Any observations]
```

### 6. Expected Results Comparison

All methods should ideally recommend the same optimal alternative, but may differ because:
- Different mathematical approaches
- Different handling of uncertainty
- Different weighting schemes

### 7. Performance Metrics to Compare

- **Speed**: Which method is fastest?
- **Consistency**: Which gives most logical results?
- **Usability**: Which is easiest to use?
- **Robustness**: Which handles edge cases best?

### 8. Sample Results Table

| Method | Time (s) | Optimal Choice | Ranking | Notes |
|--------|----------|----------------|---------|-------|
| AHP | 2.34 | iPhone 15 | 1.iPhone 2.Samsung 3.Pixel 4.OnePlus | Most comprehensive |
| Binary | 0.87 | Samsung Galaxy | 1.Samsung 2.iPhone 3.Pixel 4.OnePlus | Simple but effective |
| Experts | 1.56 | Google Pixel | 1.Pixel 2.OnePlus 3.Samsung 4.iPhone | Uses expert knowledge |
| Laplace | 0.92 | iPhone 15 | 1.iPhone 2.Samsung 3.Pixel 4.OnePlus | Equal probability |
| Maximin | 0.89 | OnePlus 12 | 1.OnePlus 2.Pixel 3.Samsung 4.iPhone | Conservative |
| Savage | 0.94 | Samsung Galaxy | 1.Samsung 2.iPhone 3.Pixel 4.OnePlus | Minimizes regret |
| Hurwitz | 0.91 | iPhone 15 | 1.iPhone 2.Samsung 3.Pixel 4.OnePlus | Balanced optimism |

### 9. Analysis Questions

1. **Which method is fastest?** (Performance)
2. **Which method gives the most logical result?** (Quality)
3. **Which method is most consistent?** (Reliability)
4. **Which method is easiest to understand?** (Usability)
5. **Which method handles uncertainty best?** (Robustness)

### 10. Next Steps After Testing

1. **Analyze** the results
2. **Identify** the best performing method
3. **Document** findings
4. **Consider** improvements
5. **Update** system recommendations

---

## 🔧 Quick Start Commands

```bash
# Start Flask app
python app.py

# Open browser
open http://localhost:5050

# Register/login to your account
# Then test each method using the files in test_files/
```

**Happy Testing!** 🚀
