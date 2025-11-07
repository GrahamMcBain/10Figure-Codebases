"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import shutil
from pathlib import Path


def pytest_configure():
    """Configure pytest markers."""
    pytest.mark.slow = pytest.mark.slow


@pytest.fixture(scope="session")
def sample_repos():
    """Create sample repository structures for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        
        # Create Go repository
        go_repo = base_dir / "go-repo"
        go_repo.mkdir()
        
        (go_repo / "go.mod").write_text("module example.com/test\n\ngo 1.21\n")
        
        # Package structure
        pkg_dir = go_repo / "pkg" / "api"
        pkg_dir.mkdir(parents=True)
        
        (pkg_dir / "handler.go").write_text("""
package api

import (
    "fmt"
    "net/http"
)

// ProcessRequest handles incoming requests
func ProcessRequest(w http.ResponseWriter, r *http.Request) {
    data := r.URL.Query().Get("data")
    result := processData(data)
    fmt.Fprintf(w, "Result: %s", result)
}

func processData(input string) string {
    return fmt.Sprintf("processed-%s", input)
}

type RequestHandler struct {
    config Config
}

func (h *RequestHandler) Handle(req *http.Request) string {
    return h.config.Process(req.URL.String())
}
""")
        
        (pkg_dir / "config.go").write_text("""
package api

type Config struct {
    Timeout int
    Debug   bool
}

func (c *Config) Process(input string) string {
    if c.Debug {
        return fmt.Sprintf("debug: %s", input)
    }
    return input
}
""")
        
        # Create Python repository
        py_repo = base_dir / "python-repo"
        py_repo.mkdir()
        
        (py_repo / "setup.py").write_text("""
from setuptools import setup
setup(name='test-package', version='1.0.0')
""")
        
        src_dir = py_repo / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        
        (src_dir / "__init__.py").write_text("")
        
        (src_dir / "handlers.py").write_text("""
import json
from typing import Dict, Any


class RequestProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def process_request(self, data: str) -> str:
        '''Process incoming request data.'''
        if self.config.get('debug'):
            return f"debug: {data}"
        return self.transform_data(data)
    
    def transform_data(self, data: str) -> str:
        return f"transformed-{data}"


def handle_api_call(endpoint: str, payload: Dict) -> Dict:
    processor = RequestProcessor({'debug': True})
    result = processor.process_request(json.dumps(payload))
    return {'status': 'ok', 'result': result}
""")
        
        (src_dir / "utils.py").write_text("""
def format_response(data):
    return {'formatted': data, 'timestamp': '2023-01-01'}

class Logger:
    def __init__(self, level='INFO'):
        self.level = level
    
    def log(self, message):
        print(f"[{self.level}] {message}")
""")
        
        yield {
            'go_repo': go_repo,
            'python_repo': py_repo,
            'base_dir': base_dir
        }


@pytest.fixture
def mini_corpus(sample_repos):
    """Create a minimal corpus for testing transforms."""
    return sample_repos
