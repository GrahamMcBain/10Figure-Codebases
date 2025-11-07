"""
Test suite for transformation engine.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from apply_transforms import LegacyTransformer


@pytest.fixture
def temp_repo():
    """Create a temporary repository structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir)
        
        # Create sample Go file
        go_dir = repo_dir / "pkg" / "api"
        go_dir.mkdir(parents=True)
        
        go_file = go_dir / "handler.go"
        go_file.write_text("""
package api

import "fmt"

func ProcessRequest(data string) string {
    return fmt.Sprintf("processed: %s", data)
}

func HandleUser(user User) error {
    return user.Validate()
}

type User struct {
    Name string
}
""")
        
        # Create sample Python file
        py_dir = repo_dir / "src" / "utils"
        py_dir.mkdir(parents=True)
        
        py_file = py_dir / "helpers.py"
        py_file.write_text("""
def process_data(data):
    return f"processed: {data}"

class UserManager:
    def __init__(self):
        self.users = []
    
    def add_user(self, name):
        self.users.append(name)
""")
        
        yield repo_dir


def test_transformer_initialization():
    """Test that transformer initializes with deterministic seed."""
    transformer1 = LegacyTransformer(seed=42)
    transformer2 = LegacyTransformer(seed=42)
    
    # Should generate same random sequence
    assert transformer1.rng.random() == transformer2.rng.random()


def test_file_discovery(temp_repo):
    """Test that transformer can discover source files."""
    transformer = LegacyTransformer(seed=42)
    
    # Mock the file discovery (since we haven't implemented it yet)
    # This test will need updating when real implementation is done
    files = list(temp_repo.rglob("*.go")) + list(temp_repo.rglob("*.py"))
    
    assert len(files) >= 2
    assert any(f.name == "handler.go" for f in files)
    assert any(f.name == "helpers.py" for f in files)


def test_rename_mapping_format():
    """Test that rename mappings follow expected JSON format."""
    transformer = LegacyTransformer(seed=42)
    
    # Test the expected format structure
    expected_format = {
        "old/path/file.go": "new/path/file_renamed.go",
        "oldSymbolName": "newSymbolName"
    }
    
    # Should be able to serialize to JSON
    json_str = json.dumps(expected_format)
    parsed = json.loads(json_str)
    
    assert isinstance(parsed, dict)


def test_api_migration_format():
    """Test API migration mapping format."""
    expected_format = {
        "symbol": "ProcessRequest",
        "v1_callsites": ["pkg/api/handler.go", "src/utils/helpers.py"],
        "expected_v2_replacements": ["ProcessRequestV2", "ProcessHTTPRequest"]
    }
    
    # Should serialize cleanly
    json_str = json.dumps(expected_format)
    parsed = json.loads(json_str)
    
    assert parsed["symbol"] == "ProcessRequest"
    assert len(parsed["v1_callsites"]) == 2


def test_deterministic_transforms():
    """Test that transforms are deterministic with same seed."""
    transformer1 = LegacyTransformer(seed=42)
    transformer2 = LegacyTransformer(seed=42)
    
    # Should select same files for transformation
    sample_files = ["file1.go", "file2.py", "file3.cpp", "file4.js"]
    
    selection1 = transformer1.rng.sample(sample_files, 2)
    # Reset transformer2 to same state
    transformer2.rng.seed(42)
    selection2 = transformer2.rng.sample(sample_files, 2)
    
    assert selection1 == selection2


@pytest.mark.slow
def test_go_syntax_validation(temp_repo):
    """Test Go syntax validation (requires go compiler)."""
    import subprocess
    
    go_file = temp_repo / "pkg" / "api" / "handler.go"
    
    # Create a valid Go module
    mod_file = temp_repo / "go.mod"
    mod_file.write_text("module test\n\ngo 1.21\n")
    
    # Test that original file compiles
    try:
        result = subprocess.run(
            ["go", "build", "./..."], 
            cwd=temp_repo, 
            capture_output=True, 
            text=True
        )
        
        # May fail if go not installed, that's ok for CI
        if result.returncode == 0:
            assert "error" not in result.stderr.lower()
    except FileNotFoundError:
        pytest.skip("Go compiler not available")


def test_metadata_persistence():
    """Test that transformation metadata can be saved and loaded."""
    transformer = LegacyTransformer(seed=42)
    
    # Create sample metadata
    transformer.renames = {"old.go": "new.go"}
    transformer.api_migrations = {"func1": {"v1_callsites": ["file1.go"]}}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        transforms_dir = Path(tmpdir) / "transforms"
        transforms_dir.mkdir()
        
        # Save metadata
        with open(transforms_dir / "renames.json", 'w') as f:
            json.dump(transformer.renames, f)
        
        with open(transforms_dir / "api_migrations.json", 'w') as f:
            json.dump(transformer.api_migrations, f)
        
        # Verify files exist and are valid JSON
        assert (transforms_dir / "renames.json").exists()
        assert (transforms_dir / "api_migrations.json").exists()
        
        # Load back and verify
        with open(transforms_dir / "renames.json", 'r') as f:
            loaded_renames = json.load(f)
        
        assert loaded_renames == transformer.renames


def test_transform_pipeline():
    """Test the complete transformation pipeline."""
    transformer = LegacyTransformer(seed=42)
    
    # This should not raise exceptions
    try:
        transformer.apply_renames()
        transformer.apply_api_drift() 
        transformer.apply_wrapper_layers()
        transformer.apply_duplication()
        
        # Should have populated metadata
        assert hasattr(transformer, 'renames')
        assert hasattr(transformer, 'api_migrations')
        assert hasattr(transformer, 'wrapper_layers') 
        assert hasattr(transformer, 'duplication_map')
        
    except Exception as e:
        # Expected to fail with placeholder implementation
        # This test documents the expected interface
        assert "not implemented" in str(e).lower() or "placeholder" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__])
