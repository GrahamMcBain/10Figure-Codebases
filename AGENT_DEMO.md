# AI Agent Demo: Legacy Codebase Benchmark

This file contains everything needed for an AI agent to demonstrate the Legacy Codebase Benchmark Corpus.

## Quick Setup

```bash
# Clone and setup (anyone can run this)
git clone https://github.com/GrahamMcBain/10Figure-Codebases.git
cd 10Figure-Codebases
make install
make build-corpus-small  # Faster version for demo
make generate-tasks
```

## Prompt for AI Agent

Copy this prompt and give it to any AI coding agent:

---

**AI AGENT BENCHMARK DEMO PROMPT:**

You are an AI coding agent being evaluated on the Legacy Codebase Performance Benchmark Corpus. This benchmark tests your ability to work with realistic legacy codebases that have undergone transformations like symbol renames, API drift, wrapper layers, and code duplication.

**YOUR MISSION:** Complete the benchmark tasks and get scored by the real scoring engine.

**STEP 1: Understand Your Environment**
You are in a directory containing:
- `src/` - Transformed legacy codebases (Kubernetes, Envoy, Django, TensorFlow)
- `tasks/` - 4 benchmark tasks you need to complete
- `scripts/validate_patch.py` - Real scoring engine (no mocks!)

**STEP 2: Examine the Tasks**
Run these commands to understand what you need to do:

```bash
# See all available tasks
ls tasks/*.yaml

# Read each task description
cat tasks/cross_file_reasoning_01.yaml
cat tasks/refactor_rename_01.yaml  
cat tasks/api_upgrade_01.yaml
cat tasks/bug_localization_01.yaml
```

**STEP 3: Complete Each Task**

### Task A: Cross-File Reasoning
**Goal:** Trace the call path for `FooMethod` through wrapper layers to find the actual implementation.

**Your Action:**
1. Search for `FooMethod` in the codebase
2. Follow the call chain through any wrappers/interfaces  
3. Find the final implementation file and function
4. Create a reasoning file documenting your analysis:

```bash
cat > REASONING.md << 'EOF'
# Cross-File Reasoning Analysis

## Task: Trace FooMethod Call Path

### Analysis Process:
[Describe how you searched and analyzed]

### Call Chain Discovered:
1. Entry Point: [file:line - function name]
2. Interface Layer: [file:line - interface/wrapper]  
3. Implementation: [file:line - actual implementation]

### Final Implementation Location:
- File: [exact file path]
- Function: [exact function name]
- Lines: [line range]

### Reasoning:
[Explain how you traced the path and verified the implementation]
EOF
```

### Task B: Refactor/Rename
**Goal:** Rename the symbol `ProcessRequest` to `HandleRequest` everywhere in the codebase.

**Your Action:**
1. Search for all occurrences of `ProcessRequest`
2. Create a patch that renames it consistently
3. Make sure to update function definitions, calls, comments, etc.

```bash
# Search for the symbol
grep -r "ProcessRequest" src/ | head -10

# Create your rename patch
# (Use your preferred method: sed, manual editing, etc.)
# Save the changes as a git diff:
git diff > refactor_rename_solution.diff
```

### Task C: API Upgrade  
**Goal:** Upgrade `FooMethod(param1, param2)` calls to `FooMethodV2(param1, param2, options={})`

**Your Action:**
1. Find all `FooMethod` callsites
2. Upgrade them to the new `FooMethodV2` signature
3. Note: Only upgrade ~60% (some should stay v1 for legacy compatibility)

```bash
# Find callsites
grep -r "FooMethod\(" src/ | head -10

# Create upgrade patch
git diff > api_upgrade_solution.diff
```

### Task D: Bug Localization
**Goal:** Find and fix the null pointer exception in request processing.

**Your Action:**
1. Look for potential null pointer issues in request processing code
2. Create a bug analysis report
3. Implement a fix

```bash
cat > BUG_ANALYSIS.md << 'EOF'
# Bug Localization Analysis

## Error Description:
NullPointerException in request processing

## Investigation Process:
[Describe your debugging approach]

## Bug Location:
- File: [exact file path]
- Line Range: [start-end lines]
- Root Cause: [specific issue found]

## Proposed Fix:
[Describe the fix you implemented]
EOF

# Create fix patch
git diff > bug_fix_solution.diff
```

**STEP 4: Combine Your Solutions**
Create a single patch with all your changes:

```bash
# Combine all your changes into one patch
git add .
git commit -m "AI Agent Solutions: Cross-file reasoning, refactor, API upgrade, bug fix"
git show HEAD > complete_agent_solution.diff
```

**STEP 5: Get Scored by Real Engine**
Run the actual scoring system (no mocks!):

```bash
# Run real validation with 10 minute timeout
python3 scripts/validate_patch.py complete_agent_solution.diff --timeout 10 --output my_results.json

# View your scores
echo "=== MY BENCHMARK RESULTS ==="
cat my_results.json | python3 -m json.tool

# Check individual task performance
echo "=== DETAILED BREAKDOWN ==="
jq '.task_results[] | {task_id, score, details}' my_results.json 2>/dev/null || python3 -c "
import json
with open('my_results.json') as f: 
    data = json.load(f)
    for task in data['task_results']:
        print(f'Task: {task[\"task_id\"]}')
        print(f'Score: {task[\"score\"]:.3f}')
        print(f'Details: {task[\"details\"]}')
        print('---')
"
```

**STEP 6: Interpret Your Results**

Your benchmark score will show:
- **Overall Score** (0.0-1.0): Weighted average across all tasks
- **Individual Task Scores**: How well you did on each challenge  
- **Detailed Metrics**: Files modified, compilation success, accuracy measures
- **Performance Level**: 
  - 0.9-1.0: Expert level 🏆
  - 0.75-0.89: Proficient ✅  
  - 0.6-0.74: Competent ✓
  - 0.4-0.59: Developing ⚠️
  - 0.0-0.39: Novice ❌

**SUCCESS CRITERIA:**
- Score > 0.5: You successfully navigated the legacy codebase
- Score > 0.75: You demonstrate strong code understanding capabilities  
- Score > 0.9: You rival expert human performance

**YOUR CHALLENGE:** Try to achieve the highest score possible by carefully analyzing the transformed legacy codebase and providing accurate solutions to each task type.

Good luck! This benchmark uses real language analysis and compilation validation - no shortcuts or mocked scoring.

---

## Expected Agent Workflow

A successful agent should:

1. **Explore the environment** - Use `ls`, `find`, `grep` to understand the codebase structure
2. **Read task descriptions** - Understand what each YAML task is asking for
3. **Analyze the code** - Use search tools to trace call paths, find symbols, identify issues
4. **Create solutions** - Write reasoning files, generate patches, implement fixes
5. **Test and validate** - Run the scoring engine to get real feedback
6. **Iterate if needed** - Use the detailed scoring output to improve solutions

The agent will get **real scores** based on:
- **Accuracy** of call path tracing
- **Completeness** of symbol renaming  
- **Correctness** of API upgrades
- **Precision** of bug localization

This is a legitimate test of AI coding capabilities on realistic legacy codebase challenges!
