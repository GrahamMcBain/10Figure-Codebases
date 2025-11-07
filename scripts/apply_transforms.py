#!/usr/bin/env python3
"""
Apply synthetic transformations to create legacy codebase conditions.

This script applies various transformations to the imported repositories:
1. Symbol & file renames with real language parsing
2. API drift simulation with v1/v2 versions
3. Wrapper/indirection layers
4. Code duplication with modifications
"""

import os
import json
import random
import argparse
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import yaml

# Import the real transformation engine
try:
    from transform_engine import FileIndex, SymbolRenamer, APIDriftSimulator, LanguageValidator
except ImportError:
    logger.error("transform_engine module not found. Please ensure transform_engine.py is in the same directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LegacyTransformer:
    """Applies real legacy codebase transformations using language-aware parsing."""
    
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.seed = seed
        
        # Initialize transformation results
        self.renames = {}
        self.api_migrations = {}
        self.wrapper_layers = {}
        self.duplication_map = {}
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.file_index = None
        self.validator = LanguageValidator()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from repos.yaml."""
        try:
            with open('repos.yaml', 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback configuration
            return {
                'transforms': {
                    'file_rename_percentage': 0.08,
                    'symbol_rename_percentage': 0.05,
                    'api_drift_functions': 10,
                    'wrapper_layers': 8,
                    'duplication_directories': 2
                }
            }
    
    def apply_all_transforms(self):
        """Apply all transformation types with real implementations."""
        logger.info("Starting legacy transformations with real language parsing...")
        
        # Build file index first
        self._build_file_index()
        
        # Apply transformations in order
        self.apply_renames()
        self.apply_api_drift() 
        self.apply_wrapper_layers()
        self.apply_duplication()
        
        # Validate results
        self._validate_transformations()
        
        # Save metadata
        self.save_transform_metadata()
        logger.info("All transformations completed!")
    
    def _build_file_index(self):
        """Build index of all source files and symbols."""
        logger.info("Building comprehensive file index...")
        
        # Find all source repositories
        src_dirs = []
        if os.path.exists('src'):
            src_dirs = [os.path.join('src', d) for d in os.listdir('src') 
                       if os.path.isdir(os.path.join('src', d))]
        
        if not src_dirs:
            logger.warning("No source directories found in src/")
            return
        
        self.file_index = FileIndex(src_dirs)
        self.file_index.build_index()
    
    def apply_renames(self):
        """Apply real file and symbol renames using language parsers."""
        if not self.file_index:
            logger.error("File index not built - skipping renames")
            return
            
        logger.info("Applying real symbol renames...")
        
        # Use the real symbol renamer
        renamer = SymbolRenamer(self.file_index, self.rng)
        
        rename_percentage = self.config['transforms']['symbol_rename_percentage']
        result = renamer.rename_symbols(rename_percentage)
        
        # Store results
        self.renames.update(result.metadata.get('rename_map', {}))
        
        if result.success:
            logger.info(f"Successfully renamed symbols in {result.files_changed} files")
        else:
            logger.warning(f"Rename completed with {len(result.errors)} errors")
            for error in result.errors[:5]:  # Show first 5 errors
                logger.warning(f"  {error}")
    
    def apply_api_drift(self):
        """Create real API drift by implementing v1/v2 library versions."""
        if not self.file_index:
            logger.error("File index not built - skipping API drift")
            return
            
        logger.info("Applying real API drift transformations...")
        
        # Use the real API drift simulator
        drift_sim = APIDriftSimulator(self.file_index, self.rng)
        
        functions_count = self.config['transforms']['api_drift_functions']
        result = drift_sim.apply_api_drift(functions_count)
        
        # Store results  
        self.api_migrations.update(result.metadata.get('api_migrations', {}))
        
        if result.success:
            logger.info(f"Applied API drift to {result.files_changed} files")
        else:
            logger.warning(f"API drift completed with {len(result.errors)} errors")
            for error in result.errors[:5]:
                logger.warning(f"  {error}")
    
    def apply_wrapper_layers(self):
        """Add real wrapper layers to create indirection for cross-file reasoning."""
        logger.info("Adding real wrapper/indirection layers...")
        
        if not self.file_index:
            logger.error("File index not built - skipping wrapper layers")
            return
        
        # Select functions to wrap
        all_symbols = list(self.file_index.symbols_to_files.keys())
        wrapper_count = self.config['transforms']['wrapper_layers']
        
        if len(all_symbols) == 0:
            logger.warning("No symbols found for wrapper creation")
            return
        
        selected_symbols = self.rng.sample(
            all_symbols, 
            min(wrapper_count, len(all_symbols))
        )
        
        files_created = 0
        
        for symbol in selected_symbols:
            try:
                symbol_files = list(self.file_index.symbols_to_files[symbol])
                if not symbol_files:
                    continue
                
                # Create wrapper in same directory as original
                original_file = symbol_files[0]
                file_info = self.file_index.files[original_file]
                
                if file_info.language in ['go', 'python']:
                    wrapper_file = self._create_wrapper_file(original_file, symbol, file_info.language)
                    if wrapper_file:
                        files_created += 1
                        self.wrapper_layers[symbol] = {
                            "original_file": original_file,
                            "wrapper_file": wrapper_file,
                            "call_chain": f"caller -> {wrapper_file} -> {original_file}"
                        }
                        
            except Exception as e:
                logger.warning(f"Failed to create wrapper for {symbol}: {e}")
        
        logger.info(f"Created {files_created} wrapper layers")
    
    def _create_wrapper_file(self, original_file: str, symbol: str, language: str) -> str:
        """Create a wrapper file for a symbol."""
        original_path = Path(original_file)
        wrapper_path = original_path.parent / f"{original_path.stem}_wrapper{original_path.suffix}"
        
        try:
            if language == 'go':
                wrapper_content = self._generate_go_wrapper(symbol, original_path.stem)
            elif language == 'python':
                wrapper_content = self._generate_python_wrapper(symbol, original_path.stem)
            else:
                return None
            
            with open(wrapper_path, 'w') as f:
                f.write(wrapper_content)
            
            logger.info(f"Created wrapper: {wrapper_path}")
            return str(wrapper_path)
            
        except Exception as e:
            logger.error(f"Failed to create wrapper file {wrapper_path}: {e}")
            return None
    
    def _generate_go_wrapper(self, symbol: str, original_module: str) -> str:
        """Generate Go wrapper code."""
        return f'''// Auto-generated wrapper for {symbol}
package main

import (
    "log"
    "time"
)

// {symbol}Wrapper provides logging and monitoring for {symbol}
func {symbol}Wrapper(args ...interface{{}}) interface{{}} {{
    start := time.Now()
    log.Printf("Calling {symbol} at %v", start)
    
    // TODO: Call original {symbol} function
    result := {symbol}(args...)
    
    duration := time.Since(start)
    log.Printf("{symbol} completed in %v", duration)
    
    return result
}}

// Logging wrapper interface
type {symbol}Logger interface {{
    Log(message string)
    Wrap(fn func(...interface{{}}) interface{{}}) func(...interface{{}}) interface{{}}
}}
'''
    
    def _generate_python_wrapper(self, symbol: str, original_module: str) -> str:
        """Generate Python wrapper code."""
        return f'''"""Auto-generated wrapper for {symbol}"""

import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

class {symbol}Wrapper:
    """Logging and monitoring wrapper for {symbol}"""
    
    def __init__(self, original_func: Callable):
        self.original_func = original_func
        self.call_count = 0
    
    def __call__(self, *args, **kwargs) -> Any:
        self.call_count += 1
        start_time = time.time()
        
        logger.info(f"Calling {symbol} (call #{{self.call_count}})")
        
        try:
            result = self.original_func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{symbol} completed in {{duration:.3f}}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{symbol} failed after {{duration:.3f}}s: {{e}}")
            raise

def create_{symbol.lower()}_wrapper(original_func: Callable) -> {symbol}Wrapper:
    """Factory function to create wrapper for {symbol}"""
    return {symbol}Wrapper(original_func)
'''
    
    def apply_duplication(self):
        """Create real code duplication by copying directories with modifications."""
        logger.info("Creating real code duplication...")
        
        # Find directories to duplicate
        duplicated_count = 0
        
        for repo_dir in ['src/kubernetes', 'src/envoy', 'src/django', 'src/tensorflow']:
            if not os.path.exists(repo_dir):
                continue
            
            # Find suitable subdirectories (not too large)
            subdirs = []
            for item in os.listdir(repo_dir):
                item_path = os.path.join(repo_dir, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    # Check size - don't duplicate huge directories
                    size = sum(len(files) for _, _, files in os.walk(item_path))
                    if size < 100:  # Less than 100 files
                        subdirs.append(item)
            
            if not subdirs:
                continue
            
            # Duplicate 1-2 directories per repo
            dup_count = min(self.config['transforms']['duplication_directories'], len(subdirs))
            dirs_to_duplicate = self.rng.sample(subdirs, dup_count)
            
            for dir_name in dirs_to_duplicate:
                original = os.path.join(repo_dir, dir_name)
                duplicate = os.path.join(repo_dir, f"{dir_name}_legacy")
                
                try:
                    if os.path.exists(duplicate):
                        shutil.rmtree(duplicate)
                    
                    shutil.copytree(original, duplicate)
                    
                    # Apply small modifications to duplicated files
                    modified_files = self._modify_duplicated_files(duplicate)
                    
                    self.duplication_map[original] = {
                        "duplicate_path": duplicate,
                        "modified_files": modified_files
                    }
                    
                    duplicated_count += 1
                    logger.info(f"Duplicated: {original} -> {duplicate}")
                    
                except Exception as e:
                    logger.warning(f"Failed to duplicate {original}: {e}")
        
        logger.info(f"Created {duplicated_count} directory duplications")
    
    def _modify_duplicated_files(self, duplicate_dir: str) -> List[str]:
        """Apply small modifications to duplicated files."""
        modified_files = []
        
        for root, _, files in os.walk(duplicate_dir):
            for filename in files:
                if filename.endswith(('.go', '.py', '.cpp', '.h')):
                    file_path = os.path.join(root, filename)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Apply minor modifications
                        original_content = content
                        
                        # Change some string literals
                        content = content.replace('"INFO"', '"DEBUG"')
                        content = content.replace("'error'", "'warn'")
                        
                        # Add legacy comments
                        if content.startswith('//') or content.startswith('#'):
                            content = f"// LEGACY VERSION - DO NOT USE\n{content}"
                        elif content.startswith('/*'):
                            content = f"/* LEGACY VERSION */\n{content}"
                        
                        # Change some numeric constants slightly  
                        import re
                        content = re.sub(r'\b1024\b', '1000', content)
                        content = re.sub(r'\b60\b', '65', content)
                        
                        if content != original_content:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            modified_files.append(file_path)
                            
                    except Exception as e:
                        logger.debug(f"Failed to modify {file_path}: {e}")
        
        return modified_files
    
    def _validate_transformations(self):
        """Validate that transformations don't break compilation."""
        logger.info("Validating transformation results...")
        
        if not self.file_index:
            logger.warning("No file index available for validation")
            return
        
        validation_results = {}
        
        # Check each repository
        for repo_dir in self.file_index.root_dirs:
            repo_name = os.path.basename(repo_dir)
            
            # Determine primary language
            go_files = len(list(Path(repo_dir).rglob("*.go")))
            py_files = len(list(Path(repo_dir).rglob("*.py")))
            cpp_files = len(list(Path(repo_dir).rglob("*.cpp")))
            
            if go_files > max(py_files, cpp_files):
                success, error = self.validator.validate_go(repo_dir)
                validation_results[repo_name] = {"language": "go", "success": success, "error": error}
            elif py_files > max(go_files, cpp_files):
                success, error = self.validator.validate_python(repo_dir)
                validation_results[repo_name] = {"language": "python", "success": success, "error": error}
            elif cpp_files > 0:
                success, error = self.validator.validate_cpp(repo_dir)
                validation_results[repo_name] = {"language": "cpp", "success": success, "error": error}
        
        # Report results
        for repo, result in validation_results.items():
            if result["success"]:
                logger.info(f"✓ {repo} ({result['language']}): Validation passed")
            else:
                logger.warning(f"✗ {repo} ({result['language']}): {result['error']}")
    
    def save_transform_metadata(self):
        """Save all transformation metadata to JSON files."""
        logger.info("Saving transformation metadata...")
        
        os.makedirs('transforms', exist_ok=True)
        
        # Save with better structure
        metadata = {
            "seed": self.seed,
            "transforms_applied": {
                "renames": len(self.renames),
                "api_migrations": len(self.api_migrations),
                "wrapper_layers": len(self.wrapper_layers),
                "duplications": len(self.duplication_map)
            }
        }
        
        with open('transforms/renames.json', 'w') as f:
            json.dump(self.renames, f, indent=2)
        
        with open('transforms/api_migrations.json', 'w') as f:
            json.dump(self.api_migrations, f, indent=2)
        
        with open('transforms/wrapper_layers.json', 'w') as f:
            json.dump(self.wrapper_layers, f, indent=2)
        
        with open('transforms/duplication_map.json', 'w') as f:
            json.dump(self.duplication_map, f, indent=2)
        
        with open('transforms/metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("Transformation metadata saved")
        logger.info(f"Summary: {metadata['transforms_applied']}")


def main():
    """Main entry point for applying transformations."""
    parser = argparse.ArgumentParser(description='Apply legacy codebase transformations')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for deterministic results')
    
    args = parser.parse_args()
    
    # Set environment for deterministic execution
    os.environ['PYTHONHASHSEED'] = '0'
    
    transformer = LegacyTransformer(seed=args.seed)
    transformer.apply_all_transforms()


if __name__ == '__main__':
    main()
