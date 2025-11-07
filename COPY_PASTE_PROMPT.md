# 🚀 One-Shot AI Agent Prompt

## Setup (Run These Commands First)
```bash
git clone https://github.com/GrahamMcBain/10Figure-Codebases.git
cd 10Figure-Codebases
./quick_demo.sh  # Sets up everything automatically
```

## Copy-Paste Prompt for Any AI Agent

**Paste this entire prompt into any AI coding agent (Claude, ChatGPT, etc.):**

---

You are being evaluated on the Legacy Codebase Performance Benchmark Corpus - a production-ready benchmark that tests AI agent performance on realistic legacy codebase challenges.

**CONTEXT:** You're in a directory with transformed legacy codebases (Kubernetes, Envoy, Django, TensorFlow) that have undergone 5,089+ symbol renames, API drift, wrapper layers, and code duplication. Your job is to complete 4 benchmark tasks and get scored by a real scoring engine (no mocks).

**QUICK START:** Run these commands to understand your environment:
```bash
# See what's available
ls -la
ls tasks/
ls src/

# Read the task descriptions  
cat tasks/cross_file_reasoning_01.yaml
cat tasks/refactor_rename_01.yaml
cat tasks/api_upgrade_01.yaml  
cat tasks/bug_localization_01.yaml
```

**TASK 1: Cross-File Reasoning**
Find the call path for `FooMethod` through wrapper layers to the actual implementation.

```bash
# Search for FooMethod
grep -r "FooMethod" src/ | head -20

# Create reasoning document
cat > REASONING.md << 'EOF'
# Cross-File Reasoning Analysis for FooMethod

## Search Process:
[Describe how you searched]

## Call Chain Found:
1. Entry: [file:line - function name]  
2. Wrapper: [file:line - wrapper/interface]
3. Implementation: [file:line - actual function]

## Final Answer:
- Implementation File: [exact path]
- Implementation Function: [exact name]
- Line Range: [start-end]

## Verification:
[How you confirmed this is the real implementation]
EOF
```

**TASK 2: Refactor/Rename**
Rename `ProcessRequest` to `HandleRequest` everywhere in the codebase.

```bash
# Find all occurrences
grep -r "ProcessRequest" src/ --include="*.go" --include="*.py" --include="*.cpp" | head -10

# Make your changes (use sed, manual editing, or your preferred method)
# Example with sed (be careful - test first):
# find src/ -name "*.go" -exec sed -i 's/ProcessRequest/HandleRequest/g' {} \;

# Create patch
git add .
git diff --cached > refactor_solution.diff
git reset  # Don't actually commit yet
```

**TASK 3: API Upgrade**
Upgrade `FooMethod(param1, param2)` calls to `FooMethodV2(param1, param2, options={})`. Only upgrade about 60% of callsites.

```bash
# Find callsites
grep -r "FooMethod(" src/ | head -10

# Make selective upgrades (your choice which ones to keep as v1)
# Create patch
git add .
git diff --cached > api_upgrade_solution.diff  
git reset
```

**TASK 4: Bug Localization**
Find and fix a null pointer exception in request processing.

```bash
# Look for potential null pointer issues
grep -r -i "null\|nil" src/ | grep -i "request\|process" | head -10

# Create bug analysis
cat > BUG_ANALYSIS.md << 'EOF'
# Bug Localization Analysis

## Error: NullPointerException in request processing

## Investigation:
[Describe your search process]

## Bug Found:
- File: [exact file path]  
- Lines: [line numbers]
- Issue: [specific problem]
- Root Cause: [why it happens]

## Fix Implemented:
[Describe your fix]
EOF

# Implement your fix and create patch
git add .
git diff --cached > bug_fix_solution.diff
git reset
```

**FINAL STEP: Combine and Score**
```bash
# Apply all your solutions
git add .
git commit -m "AI Agent Complete Solution: reasoning, refactor, API upgrade, bug fix"

# Generate final patch
git show HEAD > complete_solution.diff

# Get scored by the REAL scoring engine
python3 scripts/validate_patch.py complete_solution.diff --timeout 10 --output results.json

# View your results
echo "=== BENCHMARK RESULTS ==="
cat results.json | python3 -m json.tool

echo "=== SCORE SUMMARY ==="
python3 -c "
import json
with open('results.json') as f:
    data = json.load(f)
    print(f'Overall Score: {data[\"overall_score\"]:.3f}')
    print(f'Execution Time: {data[\"execution_time\"]:.1f}s')
    print(f'Patch Applied: {data[\"patch_applied\"]}')
    print('\\nTask Breakdown:')
    for task in data['task_results']:
        print(f'  • {task[\"task_id\"]}: {task[\"score\"]:.3f}')
        if task['errors']:
            print(f'    Errors: {task[\"errors\"]}')
"
```

**SCORING GUIDE:**
- **0.9-1.0**: Expert level - You crushed it! 🏆
- **0.75-0.89**: Proficient - Solid performance ✅
- **0.6-0.74**: Competent - Good job with room for improvement ✓  
- **0.4-0.59**: Developing - Partial success ⚠️
- **0.0-0.39**: Needs work - Try again ❌

**YOUR CHALLENGE:** Get the highest score possible by carefully analyzing the legacy codebase. The scoring engine uses real language analysis - no mocks or shortcuts!

**TIPS FOR SUCCESS:**
1. Use `find`, `grep`, `ripgrep` extensively to explore the codebase
2. Follow call chains carefully - look for interfaces, wrappers, implementations  
3. Test your changes don't break compilation (the scorer checks this)
4. Create detailed reasoning/analysis files - the scorer reads them
5. Be precise with file paths and line numbers

Good luck! This is a real test of your legacy codebase navigation abilities.

---

**Expected outcome:** You should get scored on 4 different tasks using actual language analysis and receive a detailed breakdown of your performance on each challenge type.
