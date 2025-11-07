.PHONY: build-corpus generate-tasks score-patch clean help

# Default target
help:
	@echo "Legacy Codebase Benchmark Corpus"
	@echo ""
	@echo "Available targets:"
	@echo "  build-corpus    - Clone repos and apply transformations"
	@echo "  generate-tasks  - Generate benchmark tasks and ground truth"
	@echo "  score-patch     - Validate and score a patch (requires PATCH=path/to/patch.diff)"
	@echo "  clean          - Remove generated files and imported repos"
	@echo "  help           - Show this help message"

# Build the corpus by importing repos and applying transformations
build-corpus:
	@echo "Building legacy codebase corpus..."
	python3 scripts/import_repos.py
	python3 scripts/apply_transforms.py
	@echo "Corpus build complete!"

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
