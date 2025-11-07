# Legacy Codebase Performance Benchmark Corpus

A public, reproducible benchmark for evaluating AI agent performance on legacy codebase tasks. This corpus simulates real-world legacy conditions by combining large open-source repositories and applying synthetic transformations that introduce complexity typical of aging codebases.

## Overview

This benchmark helps measure how well AI agents can:
- Navigate complex, interconnected codebases
- Perform cross-file reasoning through indirection layers
- Handle API drift and inconsistent patterns
- Locate and fix bugs in unfamiliar code
- Refactor code while maintaining correctness

## Quick Start

```bash
# Clone and build the corpus
git clone <repo-url>
cd legacy-codebase-benchmark
make build-corpus

# Generate benchmark tasks
make generate-tasks

# Test an agent's patch
make score-patch PATCH=path/to/agent-generated.diff
```

## Repository Structure

```
legacy-codebase-benchmark/
├── README.md                    # This file
├── Makefile                     # Build automation
├── scripts/                     # Build and evaluation scripts
│   ├── import_repos.py         # Clone source repositories
│   ├── apply_transforms.py     # Apply legacy transformations
│   ├── generate_tasks.py       # Create benchmark tasks
│   └── validate_patch.py       # Score agent solutions
├── src/                         # Imported source repositories
│   ├── kubernetes/             # Kubernetes codebase
│   ├── envoy/                  # Envoy Proxy codebase
│   ├── django/                 # Django web framework
│   └── tensorflow/             # TensorFlow ML library
├── transforms/                  # Applied transformation metadata
│   ├── renames.json            # File and symbol renames
│   ├── api_migrations.json     # API version drift mappings
│   ├── wrapper_layers.json     # Indirection layer mappings
│   └── duplication_map.json    # Code duplication mappings
├── tasks/                       # Benchmark task definitions
│   ├── cross_file_reasoning_01.yaml
│   ├── refactor_rename_01.yaml
│   ├── api_upgrade_01.yaml
│   ├── bug_localization_01.yaml
│   └── task_summary.json
└── scoring/                     # Evaluation framework
    ├── scoring_rules.md         # Detailed scoring criteria
    └── oracle/                  # Ground truth data
        ├── expected_symbol_paths.json
        ├── expected_refactor_targets.json
        ├── expected_api_migration_results.json
        └── expected_bug_locations.json
```

## Source Repositories

The corpus combines four large, real-world codebases:

| Repository | Language | Files | Purpose |
|------------|----------|-------|---------|
| [Kubernetes](https://github.com/kubernetes/kubernetes) | Go | ~15k | Container orchestration |
| [Envoy Proxy](https://github.com/envoyproxy/envoy) | C++ | ~8k | Service mesh proxy |
| [Django](https://github.com/django/django) | Python | ~3k | Web framework |
| [TensorFlow](https://github.com/tensorflow/tensorflow) | C++/Python | ~25k | Machine learning |

*Note: Repositories use shallow clones (depth=1) to manage size.*

## Legacy Transformations

The benchmark applies synthetic transformations to simulate legacy codebase conditions:

### 1. Symbol & File Renames (5-10% of files)
- Randomly renames files and symbols
- Creates inconsistent naming patterns
- Breaks direct symbol-to-file mappings

### 2. API Drift Simulation
- Creates v1 and v2 versions of libraries
- Migrates only ~60% of callsites to v2
- Leaves inconsistent API usage patterns

### 3. Wrapper/Indirection Layers
- Inserts interface and logging wrappers
- Creates multi-hop call chains: `callsite → interface → wrapper → implementation`
- Requires cross-file reasoning to trace execution paths

### 4. Code Duplication with Drift
- Copies directories to `*-old/` variants
- Modifies 5-10 tokens per duplicated file
- Creates near-duplicate code with subtle differences

## Benchmark Tasks

The corpus includes four types of coding challenges:

### Cross-File Reasoning
**Goal:** Trace function calls through wrapper layers to find implementations
- **Example:** Find the actual implementation of `FooMethod()` through interface → wrapper → impl chain
- **Scoring:** Correct identification of call path and final implementation
- **Difficulty:** Medium (10 min time limit)

### Refactor/Rename 
**Goal:** Rename symbols and update all references across the codebase
- **Example:** Rename `ProcessRequest` to `HandleRequest` everywhere
- **Scoring:** Percentage of references correctly updated, patch cleanliness
- **Difficulty:** Hard (15 min time limit)

### API Upgrade
**Goal:** Migrate API calls from v1 to v2 across multiple files
- **Example:** Update `FooMethod(a, b)` calls to `FooMethodV2(a, b, options={})`
- **Scoring:** Percentage of expected callsites correctly upgraded
- **Difficulty:** Hard (20 min time limit)

### Bug Localization
**Goal:** Find and identify the root cause of reported bugs
- **Example:** Locate null pointer exception in request processing
- **Scoring:** Correct file + line range identification, root cause analysis
- **Difficulty:** Expert (25 min time limit)

## Usage Examples

### Building the Corpus
```bash
# Full build pipeline
make build-corpus generate-tasks

# Individual steps
make build-corpus     # Clone repos and apply transformations
make generate-tasks   # Create benchmark tasks

# Clean and rebuild
make clean
make all
```

### Running Evaluations
```bash
# Score a patch file
make score-patch PATCH=my-solution.diff

# Score with JSON output
python3 scripts/validate_patch.py my-solution.diff --output results.json

# View scoring rules
cat scoring/scoring_rules.md
```

### Examining Tasks
```bash
# List all tasks
ls tasks/*.yaml

# View a specific task
cat tasks/cross_file_reasoning_01.yaml

# Check ground truth
cat scoring/oracle/expected_symbol_paths.json
```

## Scoring System

### Task Weights
- Cross-file reasoning: 1.0× (baseline)
- Refactor rename: 1.2× (requires precision)
- API upgrade: 1.5× (complex coordination)
- Bug localization: 2.0× (highest difficulty)

### Performance Levels
- **90-100%**: Expert level
- **75-89%**: Proficient 
- **60-74%**: Competent
- **40-59%**: Developing
- **0-39%**: Novice

### Time Penalties
- 1-25% overtime: -10%
- 26-50% overtime: -25% 
- 51-100% overtime: -50%
- >100% overtime: 0 score

See [`scoring/scoring_rules.md`](scoring/scoring_rules.md) for complete details.

## Requirements

### System Requirements
- Python 3.7+
- Git
- ~5GB disk space for corpus
- ~15 minutes build time

### Python Dependencies
```bash
pip3 install PyYAML
```

### Language Tools (for validation)
The validation scripts can optionally use language-specific tools:
- Go: `go build` for syntax checking
- Python: `python -m py_compile` for syntax checking
- C++: `clang` for basic syntax validation

## Contributing

### Adding New Tasks
1. Modify `scripts/generate_tasks.py`
2. Add corresponding ground truth generators
3. Update scoring criteria in `scoring/scoring_rules.md`
4. Test with `make generate-tasks`

### Adding New Transformations
1. Extend `scripts/apply_transforms.py`
2. Add metadata tracking to JSON outputs
3. Update documentation

### Adding Source Repositories
1. Add repository config to `scripts/import_repos.py`
2. Ensure license compatibility
3. Test build pipeline

## Performance Notes

- Repository imports use shallow clones for speed
- Transformations are logged but not applied by default (for v1)
- Full corpus build completes in <15 minutes on standard hardware
- Scoring validation applies/reverts patches safely using backups

## License

This benchmark corpus is released under MIT License. Source repositories maintain their original licenses:
- Kubernetes: Apache 2.0
- Envoy: Apache 2.0  
- Django: BSD-3-Clause
- TensorFlow: Apache 2.0

## Roadmap

### v1.0 (Current)
- ✅ Four source repositories
- ✅ Basic legacy transformations
- ✅ Four task types with scoring
- ✅ Automated build pipeline

### Future Versions
- [ ] Multi-repo dependency analysis for MCP evaluation
- [ ] XL mode with Linux kernel + Chromium
- [ ] Web UI for results visualization
- [ ] Performance optimization for faster builds
- [ ] Language-specific linting integration
- [ ] Automated difficulty calibration

## Support

For questions or issues:
1. Check existing GitHub issues
2. Review [`scoring/scoring_rules.md`](scoring/scoring_rules.md) for evaluation details
3. Open a new issue with reproduction steps

---

**Built for evaluating AI agent performance on realistic legacy codebase challenges.**
