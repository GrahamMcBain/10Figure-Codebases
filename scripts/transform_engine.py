#!/usr/bin/env python3
"""
Core transformation engine for legacy codebase simulation.

This module provides language-aware transformations for creating realistic
legacy conditions in codebases.
"""

import os
import ast
import re
import json
import random
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a source file."""
    path: str
    language: str
    size_bytes: int
    line_count: int
    symbols: List[str]
    imports: List[str]


@dataclass
class TransformResult:
    """Result of applying a transformation."""
    success: bool
    files_changed: int
    errors: List[str]
    metadata: Dict[str, Any]


class FileIndex:
    """Builds and maintains an index of source files and their symbols."""
    
    def __init__(self, root_dirs: List[str]):
        self.root_dirs = root_dirs
        self.files: Dict[str, FileInfo] = {}
        self.symbols_to_files: Dict[str, Set[str]] = {}
        
    def build_index(self) -> None:
        """Build the complete file index."""
        logger.info("Building file index...")
        
        for root_dir in self.root_dirs:
            if not os.path.exists(root_dir):
                continue
                
            for file_path in self._find_source_files(root_dir):
                try:
                    file_info = self._analyze_file(file_path)
                    self.files[file_path] = file_info
                    
                    # Index symbols
                    for symbol in file_info.symbols:
                        if symbol not in self.symbols_to_files:
                            self.symbols_to_files[symbol] = set()
                        self.symbols_to_files[symbol].add(file_path)
                        
                except Exception as e:
                    logger.warning(f"Failed to analyze {file_path}: {e}")
        
        logger.info(f"Indexed {len(self.files)} files with {len(self.symbols_to_files)} unique symbols")
    
    def _find_source_files(self, root_dir: str) -> List[str]:
        """Find all source files in a directory."""
        extensions = {'.go', '.py', '.cpp', '.h', '.hpp', '.c', '.java', '.js', '.ts'}
        exclude_patterns = {
            'vendor/', 'node_modules/', 'third_party/', '.git/', 
            'test/', 'tests/', '_test.', '.test.', 'generated/'
        }
        
        files = []
        for root, dirs, filenames in os.walk(root_dir):
            # Skip excluded directories
            if any(pattern in root for pattern in exclude_patterns):
                continue
                
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    if not any(pattern in filename for pattern in exclude_patterns):
                        files.append(os.path.join(root, filename))
        
        return files
    
    def _analyze_file(self, file_path: str) -> FileInfo:
        """Analyze a single source file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        size_bytes = len(content.encode('utf-8'))
        line_count = len(content.splitlines())
        
        # Determine language
        language = self._detect_language(file_path)
        
        # Extract symbols based on language
        symbols = self._extract_symbols(content, language)
        imports = self._extract_imports(content, language)
        
        return FileInfo(
            path=file_path,
            language=language,
            size_bytes=size_bytes,
            line_count=line_count,
            symbols=symbols,
            imports=imports
        )
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        
        language_map = {
            '.go': 'go',
            '.py': 'python',
            '.cpp': 'cpp', '.cxx': 'cpp', '.cc': 'cpp',
            '.h': 'cpp', '.hpp': 'cpp', '.hxx': 'cpp',
            '.c': 'c',
            '.java': 'java',
            '.js': 'javascript',
            '.ts': 'typescript'
        }
        
        return language_map.get(ext, 'unknown')
    
    def _extract_symbols(self, content: str, language: str) -> List[str]:
        """Extract function/class/variable symbols from code."""
        symbols = []
        
        if language == 'go':
            symbols.extend(self._extract_go_symbols(content))
        elif language == 'python':
            symbols.extend(self._extract_python_symbols(content))
        elif language in ['cpp', 'c']:
            symbols.extend(self._extract_cpp_symbols(content))
        
        return symbols
    
    def _extract_go_symbols(self, content: str) -> List[str]:
        """Extract Go function and type names."""
        symbols = []
        
        # Function definitions: func FuncName(
        func_pattern = r'func\s+(\w+)\s*\('
        symbols.extend(re.findall(func_pattern, content))
        
        # Type definitions: type TypeName struct/interface
        type_pattern = r'type\s+(\w+)\s+(?:struct|interface)'
        symbols.extend(re.findall(type_pattern, content))
        
        # Method definitions: func (receiver) MethodName(
        method_pattern = r'func\s+\([^)]+\)\s+(\w+)\s*\('
        symbols.extend(re.findall(method_pattern, content))
        
        return symbols
    
    def _extract_python_symbols(self, content: str) -> List[str]:
        """Extract Python function and class names."""
        symbols = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    symbols.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    symbols.append(node.name)
                elif isinstance(node, ast.Assign):
                    # Variable assignments at module level
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            symbols.append(target.id)
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            func_pattern = r'def\s+(\w+)\s*\('
            class_pattern = r'class\s+(\w+)\s*[:(]'
            symbols.extend(re.findall(func_pattern, content))
            symbols.extend(re.findall(class_pattern, content))
        
        return symbols
    
    def _extract_cpp_symbols(self, content: str) -> List[str]:
        """Extract C++ function and class names."""
        symbols = []
        
        # Function definitions
        func_pattern = r'(?:^|\n)\s*(?:[\w:]+\s+)*(\w+)\s*\([^)]*\)\s*[{;]'
        
        # Class definitions  
        class_pattern = r'class\s+(\w+)(?:\s*:|[^;]*{)'
        
        # Struct definitions
        struct_pattern = r'struct\s+(\w+)(?:\s*:|[^;]*{)'
        
        symbols.extend(re.findall(func_pattern, content, re.MULTILINE))
        symbols.extend(re.findall(class_pattern, content))
        symbols.extend(re.findall(struct_pattern, content))
        
        # Filter out common false positives
        filtered = [s for s in symbols if len(s) > 1 and s.isalnum()]
        
        return filtered
    
    def _extract_imports(self, content: str, language: str) -> List[str]:
        """Extract import/include statements."""
        imports = []
        
        if language == 'go':
            import_pattern = r'import\s+(?:"([^"]+)"|`([^`]+)`)'
            matches = re.findall(import_pattern, content)
            imports.extend([m[0] or m[1] for m in matches])
        elif language == 'python':
            import_pattern = r'(?:^|\n)\s*(?:import|from)\s+(\S+)'
            imports.extend(re.findall(import_pattern, content, re.MULTILINE))
        elif language in ['cpp', 'c']:
            include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
            imports.extend(re.findall(include_pattern, content))
        
        return imports


class LanguageValidator:
    """Validates that code compiles after transformations."""
    
    def validate_go(self, repo_path: str) -> Tuple[bool, str]:
        """Validate Go code compilation."""
        try:
            result = subprocess.run(
                ['go', 'build', './...'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stderr
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, "Go compiler not available or timeout"
    
    def validate_python(self, repo_path: str) -> Tuple[bool, str]:
        """Validate Python code syntax."""
        errors = []
        for py_file in Path(repo_path).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"{py_file}: {e}")
        
        return len(errors) == 0, "; ".join(errors)
    
    def validate_cpp(self, repo_path: str) -> Tuple[bool, str]:
        """Validate C++ code syntax (basic check)."""
        try:
            # Find a C++ file to test
            cpp_files = list(Path(repo_path).rglob("*.cpp"))[:5]  # Test sample
            
            for cpp_file in cpp_files:
                result = subprocess.run(
                    ['clang', '-fsyntax-only', str(cpp_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    return False, result.stderr
            
            return True, ""
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, "C++ compiler not available or timeout"


class SymbolRenamer:
    """Handles symbol renaming across files."""
    
    def __init__(self, file_index: FileIndex, rng: random.Random):
        self.file_index = file_index
        self.rng = rng
        self.rename_map: Dict[str, str] = {}
    
    def rename_symbols(self, percentage: float = 0.05) -> TransformResult:
        """Rename symbols across the codebase."""
        logger.info(f"Renaming {percentage*100:.1f}% of symbols...")
        
        # Select symbols to rename
        all_symbols = list(self.file_index.symbols_to_files.keys())
        symbol_count = max(1, int(len(all_symbols) * percentage))
        symbols_to_rename = self.rng.sample(all_symbols, min(symbol_count, len(all_symbols)))
        
        files_changed = 0
        errors = []
        
        for symbol in symbols_to_rename:
            try:
                new_name = self._generate_new_name(symbol)
                self.rename_map[symbol] = new_name
                
                # Rename in all files that contain this symbol
                affected_files = self.file_index.symbols_to_files[symbol]
                for file_path in affected_files:
                    if self._rename_in_file(file_path, symbol, new_name):
                        files_changed += 1
                        
            except Exception as e:
                errors.append(f"Failed to rename {symbol}: {e}")
        
        return TransformResult(
            success=len(errors) == 0,
            files_changed=files_changed,
            errors=errors,
            metadata={"rename_map": self.rename_map}
        )
    
    def _generate_new_name(self, original: str) -> str:
        """Generate a new name for a symbol."""
        suffixes = ["Renamed", "Legacy", "V2", "Updated", "New", "Modified"]
        prefixes = ["Old", "Legacy", "Compat", "Wrapper"]
        
        if self.rng.random() < 0.7:
            return f"{original}_{self.rng.choice(suffixes)}"
        else:
            return f"{self.rng.choice(prefixes)}_{original}"
    
    def _rename_in_file(self, file_path: str, old_name: str, new_name: str) -> bool:
        """Rename symbol in a specific file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            file_info = self.file_index.files[file_path]
            
            if file_info.language == 'go':
                content = self._rename_go_symbol(content, old_name, new_name)
            elif file_info.language == 'python':
                content = self._rename_python_symbol(content, old_name, new_name)
            elif file_info.language in ['cpp', 'c']:
                content = self._rename_cpp_symbol(content, old_name, new_name)
            else:
                # Fallback: simple text replacement with word boundaries
                pattern = r'\b' + re.escape(old_name) + r'\b'
                content = re.sub(pattern, new_name, content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rename {old_name} in {file_path}: {e}")
            return False
    
    def _rename_go_symbol(self, content: str, old_name: str, new_name: str) -> str:
        """Rename symbol in Go code."""
        # Function definitions
        content = re.sub(
            rf'\bfunc\s+{re.escape(old_name)}\s*\(',
            f'func {new_name}(',
            content
        )
        
        # Method definitions
        content = re.sub(
            rf'\bfunc\s+\([^)]+\)\s+{re.escape(old_name)}\s*\(',
            lambda m: m.group(0).replace(old_name, new_name),
            content
        )
        
        # Type definitions
        content = re.sub(
            rf'\btype\s+{re.escape(old_name)}\s+',
            f'type {new_name} ',
            content
        )
        
        # Function calls and references
        content = re.sub(
            rf'\b{re.escape(old_name)}\b',
            new_name,
            content
        )
        
        return content
    
    def _rename_python_symbol(self, content: str, old_name: str, new_name: str) -> str:
        """Rename symbol in Python code."""
        # Class definitions
        content = re.sub(
            rf'\bclass\s+{re.escape(old_name)}\s*[:(]',
            lambda m: m.group(0).replace(old_name, new_name),
            content
        )
        
        # Function definitions
        content = re.sub(
            rf'\bdef\s+{re.escape(old_name)}\s*\(',
            f'def {new_name}(',
            content
        )
        
        # References
        content = re.sub(
            rf'\b{re.escape(old_name)}\b',
            new_name,
            content
        )
        
        return content
    
    def _rename_cpp_symbol(self, content: str, old_name: str, new_name: str) -> str:
        """Rename symbol in C++ code."""
        # Simple word boundary replacement for C++
        pattern = rf'\b{re.escape(old_name)}\b'
        return re.sub(pattern, new_name, content)


class APIDriftSimulator:
    """Simulates API version drift by creating v1/v2 versions."""
    
    def __init__(self, file_index: FileIndex, rng: random.Random):
        self.file_index = file_index
        self.rng = rng
        self.api_migrations: Dict[str, Any] = {}
    
    def apply_api_drift(self, functions_per_repo: int = 5) -> TransformResult:
        """Apply API drift simulation."""
        logger.info(f"Applying API drift simulation...")
        
        # Select functions to create v2 versions for
        all_symbols = [s for s in self.file_index.symbols_to_files.keys() 
                      if len(s) > 3 and s[0].isupper()]  # Likely function names
        
        selected_symbols = self.rng.sample(
            all_symbols, 
            min(functions_per_repo, len(all_symbols))
        )
        
        files_changed = 0
        errors = []
        
        for symbol in selected_symbols:
            try:
                # Create v2 version of the API
                v2_symbol = f"{symbol}V2"
                
                # Find files containing this symbol
                symbol_files = list(self.file_index.symbols_to_files[symbol])
                
                if not symbol_files:
                    continue
                
                # Create v2 definition in first file
                definition_file = symbol_files[0]
                if self._create_v2_definition(definition_file, symbol, v2_symbol):
                    files_changed += 1
                
                # Migrate 60% of callsites to v2
                usage_files = symbol_files[1:] if len(symbol_files) > 1 else []
                migrated_count = int(len(usage_files) * 0.6)
                files_to_migrate = self.rng.sample(usage_files, min(migrated_count, len(usage_files)))
                
                for file_path in files_to_migrate:
                    if self._migrate_callsite(file_path, symbol, v2_symbol):
                        files_changed += 1
                
                # Record the migration
                self.api_migrations[symbol] = {
                    "v2_symbol": v2_symbol,
                    "definition_file": definition_file,
                    "total_callsites": len(usage_files),
                    "migrated_callsites": len(files_to_migrate),
                    "migrated_files": files_to_migrate
                }
                
            except Exception as e:
                errors.append(f"Failed to apply API drift for {symbol}: {e}")
        
        return TransformResult(
            success=len(errors) == 0,
            files_changed=files_changed,
            errors=errors,
            metadata={"api_migrations": self.api_migrations}
        )
    
    def _create_v2_definition(self, file_path: str, old_symbol: str, new_symbol: str) -> bool:
        """Create a v2 definition of a function/method."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            file_info = self.file_index.files[file_path]
            
            if file_info.language == 'go':
                content = self._add_go_v2_function(content, old_symbol, new_symbol)
            elif file_info.language == 'python':
                content = self._add_python_v2_function(content, old_symbol, new_symbol)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create v2 definition in {file_path}: {e}")
            return False
    
    def _add_go_v2_function(self, content: str, old_symbol: str, new_symbol: str) -> str:
        """Add v2 version of Go function."""
        # Find the original function definition
        func_pattern = rf'(func\s+{re.escape(old_symbol)}\s*\([^)]*\)\s*[^{{]*\{{[^}}]*\}})'
        
        match = re.search(func_pattern, content, re.DOTALL)
        if match:
            original_func = match.group(1)
            v2_func = original_func.replace(f'func {old_symbol}', f'func {new_symbol}')
            
            # Add v2 function after the original
            content = content.replace(original_func, f"{original_func}\n\n{v2_func}")
        
        return content
    
    def _add_python_v2_function(self, content: str, old_symbol: str, new_symbol: str) -> str:
        """Add v2 version of Python function."""
        # Find the original function definition
        func_pattern = rf'(def\s+{re.escape(old_symbol)}\s*\([^)]*\):[^\n]*(?:\n(?:    [^\n]*|\n)*)*)'
        
        match = re.search(func_pattern, content, re.MULTILINE)
        if match:
            original_func = match.group(1)
            v2_func = original_func.replace(f'def {old_symbol}', f'def {new_symbol}')
            
            # Add v2 function after the original
            content = content.replace(original_func, f"{original_func}\n\n{v2_func}")
        
        return content
    
    def _migrate_callsite(self, file_path: str, old_symbol: str, new_symbol: str) -> bool:
        """Migrate a callsite from v1 to v2 API."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Simple replacement of function calls
            pattern = rf'\b{re.escape(old_symbol)}\b'
            new_content = re.sub(pattern, new_symbol, content)
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to migrate callsite in {file_path}: {e}")
            return False


def main():
    """Test the transformation engine."""
    # This is a standalone test - the real integration happens in apply_transforms.py
    print("Transform engine loaded successfully!")
    
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "test":
        # Run a quick test
        test_dirs = ["src/"]
        if any(os.path.exists(d) for d in test_dirs):
            index = FileIndex(test_dirs)
            index.build_index()
            print(f"Found {len(index.files)} files with {len(index.symbols_to_files)} symbols")


if __name__ == "__main__":
    main()
