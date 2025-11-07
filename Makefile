.PHONY: build-corpus build-corpus-small generate-tasks score-patch clean help test install

# Default target
help:
	@echo "Legacy Codebase Benchmark Corpus"
	@echo ""
	@echo "Available targets:"
	@echo "  install         - Install Python dependencies"
	@echo "  test           - Run test suite"
	@echo "  build-corpus    - Clone repos and apply transformations (full)"
	@echo "  build-corpus-small - Build with core repos only (for CI)"
	@echo "  generate-tasks  - Generate benchmark tasks and ground truth"
	@echo "  score-patch     - Validate and score a patch (requires PATCH=path/to/patch.diff)"
	@echo "  clean          - Remove generated files and imported repos"
	@echo "  help           - Show this help message"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip3 install -r requirements.txt

# Run test suite
test:
	@echo "Running test suite..."
	pytest tests/ -v

# Run linting
lint:
	@echo "Running code quality checks..."
	black --check scripts/ tests/
	ruff check scripts/ tests/
	mypy scripts/ --ignore-missing-imports

# Build the corpus by importing repos and applying transformations
build-corpus:
	@echo "Building legacy codebase corpus..."
	PYTHONHASHSEED=0 python3 scripts/import_repos.py --seed=42
	PYTHONHASHSEED=0 python3 scripts/apply_transforms.py --seed=42
	@echo "Corpus build complete!"

# Build smaller corpus for CI/testing
build-corpus-small:
	@echo "Building small corpus (core repos only)..."
	PYTHONHASHSEED=0 python3 scripts/import_repos.py --seed=42 --core-only
	PYTHONHASHSEED=0 python3 scripts/apply_transforms.py --seed=42
	@echo "Small corpus build complete!"

# Generate benchmark tasks and ground truth data
generate-tasks:
	@echo "Generating benchmark tasks..."
	python3 scripts/generate_tasks.py
	@echo "Task generation complete!"

# Validate and score a patch
score-patch:
ifndef PATCH
	@echo "Error: PATCH parameter required"
	@echo "Usage: make score-patch PATCH=path/to/patch.diff"
	@exit 1
endif
	@echo "Scoring patch: $(PATCH)"
	python3 scripts/validate_patch.py $(PATCH)

# Clean up generated files
clean:
	@echo "Cleaning up..."
	rm -rf src/*/
	rm -rf transforms/*.json
	rm -rf tasks/*.yaml
	rm -rf scoring/oracle/*.json
	@echo "Cleanup complete!"

# Full pipeline
all: build-corpus generate-tasks
	@echo "Full pipeline complete!"
