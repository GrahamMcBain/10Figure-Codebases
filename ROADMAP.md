# Implementation Roadmap: Legacy Codebase Benchmark Corpus

Based on Oracle analysis, this document outlines the path from current scaffolding to production-ready benchmark.

## Current State Assessment

✅ **What Works:**
- Repository structure and documentation
- Basic cloning pipeline (4 repos)
- Task generation framework  
- Scoring infrastructure skeleton

❌ **Critical Gaps:**
- Transformation engine is placeholder-only
- No real file/symbol manipulation
- Limited scale (4 repos vs 1000+ target)
- No Sourcegraph MCP integration
- Validation doesn't actually verify transformations

## Guiding Principles

1. **Deterministic** - Fixed seeds, reproducible builds
2. **Realistic** - Code must compile/test after transforms
3. **Observable** - Structured logging for MCP integration
4. **Scalable** - Handle 10-100M LoC efficiently
5. **Extensible** - Add languages/repos via manifests

## Implementation Phases

### Phase 1: Working Corpus (Weeks 1-2) ⭑ CRITICAL

#### 1.1 Transform Engine Implementation
**File:** `scripts/apply_transforms.py`

```python
# Add real language-aware transformations:
class TransformEngine:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.file_index = self._build_index()
    
    def rename_symbols(self, percentage=0.1):
        # Go: use go/parser + go/format
        # Python: use ast module
        # C++: use libclang bindings
        
    def inject_api_drift(self, apis_per_repo=5):
        # Create v1/v2 dirs with sig changes
        # Update 60% of callsites to v2
        
    def add_wrapper_layers(self, functions_to_wrap=10):
        # Interface + LoggingWrapper pattern
        # Cross-package indirection
```

**Dependencies to add:**
```bash
pip3 install gitpython clang astunparse
```

#### 1.2 Deterministic Execution
- Add `--seed` flag to all scripts
- Set `PYTHONHASHSEED=0` in Makefile
- Pin tool versions in requirements.txt

#### 1.3 Compile Validation
- Add language-specific validators:
  - Go: `go build ./...`
  - Python: `python -m py_compile`
  - C++: `clang -fsyntax-only`
- Rollback transforms that break compilation

### Phase 2: Scale & Score (Weeks 3-4) ⭑ CRITICAL

#### 2.1 Multi-Repo Manifest System
**File:** `repos.yaml`

```yaml
repos:
  - name: kubernetes
    url: https://github.com/kubernetes/kubernetes
    language: go
    weight: 3
    branch: main
    depth: 1
  
  - name: pytorch
    url: https://github.com/pytorch/pytorch  
    language: cpp
    weight: 2
    
  # ... 1000+ repos
```

#### 2.2 Parallel Processing
```python
# Enhanced import_repos.py
async def clone_repo_batch(repos, concurrency=10):
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [clone_with_semaphore(repo, semaphore) for repo in repos]
    return await asyncio.gather(*tasks)
```

#### 2.3 Caching & Sharding
- Compress repos to `.tar.zst` for reuse
- Support `SHARD=1/10` environment variable
- Skip unchanged repos via SHA comparison

### Phase 3: MCP Integration (Weeks 5-6) ⭑ CRITICAL

#### 3.1 Benchmark Schema
**File:** `spec/benchmark.schema.json`

```json
{
  "corpus_id": "legacy-v1.0",
  "repositories": [...],
  "transformations": [...],
  "tasks": [...],
  "scoring_weights": {...}
}
```

#### 3.2 Sourcegraph MCP Adapter
**File:** `mcp/sourcegraph_adapter.py`

```python
class SourcegraphMCP:
    def register_corpus(self, schema_file):
        # GraphQL mutation to register benchmark
        
    def submit_task_result(self, task_id, agent_result):
        # Upload score to Sourcegraph dashboard
```

#### 3.3 Agent Runner
**File:** `mcp/runner.ts` (Node.js)

```typescript
// Executes agent in Docker container
// Collects patches and responses
// Calls validate_patch.py
// Reports to Sourcegraph
```

### Phase 4: Production Ready (Weeks 7+)

#### 4.1 Real Scoring Implementation
Replace placeholder scoring with:
- AST-based symbol rename detection
- API call pattern analysis
- Cross-file dependency tracing
- Unit test execution validation

#### 4.2 XL Corpus Support
Add mega-repositories:
- Linux kernel (20M+ lines)
- Chromium (15M+ lines) 
- LLVM (10M+ lines)

## Immediate Action Items

### Week 1 Priorities

1. **Transform Engine Foundation**
   ```bash
   # Create feature branch
   git checkout -b feat/transform-engine
   
   # Add real language parsers
   pip3 install gitpython clang astunparse go-ast-utils
   
   # Implement Go symbol renaming first
   ```

2. **Add Deterministic Seeds**
   ```python
   # In all scripts
   parser.add_argument('--seed', type=int, default=42)
   random.seed(args.seed)
   ```

3. **Create Test Infrastructure**
   ```bash
   mkdir tests/
   # Add pytest + fixtures for small test repos
   ```

### Week 2 Priorities

1. **Implement Core Transforms**
   - File/symbol rename (Go + Python)
   - API drift simulation
   - Wrapper layer injection

2. **Add Compile Validation**
   ```python
   def validate_compilation(repo_path, language):
       if language == 'go':
           return subprocess.run(['go', 'build', './...'], cwd=repo_path)
   ```

## Technical Architecture

```
┌─ Import Pipeline ─────────────────────────────┐
│  repos.yaml → parallel clone → cache (.tar)   │
└────────────┬──────────────────────────────────┘
             │
┌─ Transform Pipeline ──────────────────────────┐
│  FileIndex → Rename → APIDrift → Wrappers →   │
│  Duplication → Validation → JSON logs         │
└────────────┬──────────────────────────────────┘
             │
┌─ Task Generation ─────────────────────────────┐
│  Oracle creation → YAML tasks → Ground truth  │
└────────────┬──────────────────────────────────┘
             │
┌─ MCP Integration ─────────────────────────────┐
│  Sourcegraph registration → Agent execution → │
│  Scoring → Dashboard upload                   │
└───────────────────────────────────────────────┘
```

## Success Metrics

- [ ] Transforms 1000+ repositories in <1 hour
- [ ] 100% compilation success after transforms  
- [ ] Deterministic: identical output across runs
- [ ] Agent scores correlate with manual evaluation
- [ ] Full Sourcegraph MCP workflow functional

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Transform breaks compilation | Incremental validation + rollback |
| Memory exhaustion on large repos | Streaming, shallow clones, sharding |
| Language parser failures | Start with Go/Python, expand gradually |
| License compliance issues | SPDX tracking, permissive-only repos |

## Resource Requirements

**Development:** 1 FTE engineer + 0.5 FTE infrastructure
**Infrastructure:** 16GB RAM, 1TB SSD, 8-core CPU minimum
**Timeline:** 6-8 weeks for full production deployment

---

*This roadmap transforms the current scaffolding into a production-ready benchmark capable of rigorously evaluating AI agents on realistic legacy codebase challenges.*
