# Scoring Rules for Legacy Codebase Benchmark

This document defines the scoring criteria for different types of benchmark tasks in the legacy codebase performance evaluation.

## Task Types and Success Criteria

### 1. Cross-File Reasoning Tasks

**Success Criteria:**
- Agent correctly identifies the implementation path through wrapper layers
- Full call chain is documented from entry point to final implementation
- Correct file and function names are identified

**Scoring Formula:**
```
Score = (Correct Path Steps / Total Path Steps) × 100
```

**Partial Credit:**
- 25% - Identifies starting point correctly
- 50% - Identifies intermediate wrapper layers
- 25% - Identifies final implementation

**Examples:**
- Perfect score (100): Complete path traced through all layers
- Good score (75): Missing one intermediate layer but finds implementation
- Poor score (25): Only identifies entry point

### 2. Refactor Rename Tasks

**Success Criteria:**
- Patch applies cleanly without conflicts
- All references to the symbol are updated
- No compilation/syntax errors introduced
- No false positives (unrelated symbols renamed)

**Scoring Formula:**
```
Score = (Correctly Updated References / Total References) × Cleanliness Factor
```

Where Cleanliness Factor = 1.0 if no errors, 0.8 if minor issues, 0.5 if major issues

**Validation Steps:**
1. Apply patch to codebase
2. Run language-specific syntax checker
3. Count updated vs. missed references
4. Check for false positive changes

### 3. API Upgrade Tasks

**Success Criteria:**
- Correct number of callsites upgraded (per ground truth expectations)
- New API signature used correctly
- Legacy callsites preserved where specified
- No breaking changes introduced

**Scoring Formula:**
```
Score = (Correctly Upgraded Callsites / Expected Upgraded Callsites) × 100
```

**Note:** Not all callsites need upgrading - ground truth specifies which should remain v1 for legacy compatibility.

**Deductions:**
- -10% for each incorrectly upgraded callsite that should remain v1
- -20% for incorrect new API signature usage
- -50% if patch breaks existing functionality

### 4. Bug Localization Tasks

**Success Criteria:**
- Correct file identified
- Correct line range identified (within ±5 lines acceptable)
- Root cause correctly diagnosed
- Proposed fix addresses the actual issue

**Scoring Formula:**
```
Score = File Score (40%) + Location Score (30%) + Diagnosis Score (30%)
```

**Component Scoring:**
- File Score: 100% if correct file, 0% otherwise
- Location Score: 100% if within ±2 lines, 75% if within ±5 lines, 0% otherwise  
- Diagnosis Score: 100% if root cause correct, 50% if partially correct, 0% otherwise

## Overall Scoring

### Weighted Task Scores
Different task types have different weights based on difficulty:

| Task Type | Weight | Rationale |
|-----------|--------|-----------|
| Cross-file reasoning | 1.0x | Baseline difficulty |
| Refactor rename | 1.2x | Requires precision and completeness |
| API upgrade | 1.5x | Complex multi-file coordination |
| Bug localization | 2.0x | Highest skill requirement |

### Final Score Calculation
```
Final Score = Σ(Task Score × Task Weight) / Σ(Task Weights)
```

## Performance Thresholds

| Score Range | Performance Level | Description |
|-------------|------------------|-------------|
| 90-100% | Expert | Exceptional performance, minimal errors |
| 75-89% | Proficient | Good performance with minor issues |
| 60-74% | Competent | Acceptable performance with some gaps |
| 40-59% | Developing | Partial success, significant improvement needed |
| 0-39% | Novice | Major issues, fundamental gaps |

## Time Penalties

Tasks include maximum time limits. Penalties for exceeding time:
- 10% penalty for 1-25% overtime
- 25% penalty for 26-50% overtime  
- 50% penalty for 51-100% overtime
- 0 score for >100% overtime

## Quality Factors

Additional factors that affect scoring:

### Code Quality
- **Clean patches**: No unnecessary whitespace changes, proper formatting
- **Minimal scope**: Changes only what's necessary
- **Preservation**: Doesn't break existing functionality

### Completeness
- **Documentation**: Explanations of changes made
- **Edge cases**: Consideration of boundary conditions
- **Testing**: Verification that changes work correctly

### Efficiency
- **Direct approach**: Shortest reasonable path to solution
- **Tool usage**: Effective use of available development tools
- **Resource usage**: Reasonable time and computational resources
