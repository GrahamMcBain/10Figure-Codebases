#!/usr/bin/env python3
"""
Validate and score agent-generated patches against ground truth.

This script takes a patch file, applies it to the codebase, and scores
the results against expected outcomes defined in the ground truth data.

NOW WITH REAL SCORING ENGINE - No more placeholder/mock scores!
"""

import os
import sys
import json
import yaml
import subprocess
import logging
import argparse
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Import the real scoring engine
try:
    from scoring_engine import ScoringEngine, ScoreResult
except ImportError:
    logging.error("scoring_engine module not found. Please ensure scoring_engine.py is in the same directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PatchValidator:
    """Validates and scores patches against benchmark tasks using REAL scoring logic."""
    
    def __init__(self, patch_file: str, timeout_minutes: int = 30):
        self.patch_file = patch_file
        self.timeout_minutes = timeout_minutes
        self.backup_dir = None  # Will be a temp directory
        self.scoring_engine = ScoringEngine()
        self.results = []
    
    def validate_and_score(self) -> Dict[str, Any]:
        """Main validation and scoring pipeline with real scoring."""
        start_time = time.time()
        logger.info(f"Validating patch with REAL scoring: {self.patch_file}")
        
        try:
            # Create backup using temp directory (FIX: backup bug)
            self.create_backup()
            
            # Apply patch with timeout
            patch_applied = self.apply_patch_with_timeout()
            
            # Load and score all tasks
            tasks = self.load_tasks()
            
            if not tasks:
                return {
                    'error': 'No tasks found to score',
                    'score': 0,
                    'execution_time': time.time() - start_time
                }
            
            # Score each task with the real scoring engine
            self.results = self.scoring_engine.score_all_tasks(
                tasks, 
                os.getcwd(),  # Current working directory (corpus root)
                patch_applied
            )
            
            # Calculate weighted overall score
            overall_score = self.calculate_weighted_score()
            
            # Prepare detailed results
            result = {
                'patch_file': self.patch_file,
                'overall_score': overall_score,
                'patch_applied': patch_applied,
                'execution_time': time.time() - start_time,
                'task_results': [
                    {
                        'task_id': r.task_id,
                        'score': r.score,
                        'max_score': r.max_score,
                        'details': r.details,
                        'errors': r.errors,
                        'execution_time': r.execution_time
                    } for r in self.results
                ],
                'status': 'success'
            }
            
            # Log summary
            logger.info(f"Validation complete - Overall score: {overall_score:.3f}")
            for r in self.results:
                logger.info(f"  {r.task_id}: {r.score:.3f} ({len(r.errors)} errors)")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'error': str(e), 
                'score': 0,
                'execution_time': time.time() - start_time
            }
        
        finally:
            # Always restore from backup
            self.restore_backup()
    
    def create_backup(self):
        """Create backup of current state before applying patch."""
        logger.info("Creating backup...")
        
        # Create temporary directory for backup (FIX: backup bug)
        self.backup_dir = tempfile.mkdtemp(prefix='benchmark_backup_')
        
        # Backup src directory if it exists
        if os.path.exists('src'):
            src_backup = os.path.join(self.backup_dir, 'src')
            shutil.copytree('src', src_backup)
        
        # Backup transforms directory if it exists
        if os.path.exists('transforms'):
            transforms_backup = os.path.join(self.backup_dir, 'transforms')
            shutil.copytree('transforms', transforms_backup)
        
        # Backup any other relevant files
        for item in ['tasks', 'scoring']:
            if os.path.exists(item):
                backup_path = os.path.join(self.backup_dir, item)
                if os.path.isfile(item):
                    shutil.copy2(item, backup_path)
                else:
                    shutil.copytree(item, backup_path)
        
        logger.info(f"Backup created successfully at {self.backup_dir}")
    
    def apply_patch_with_timeout(self) -> bool:
        """Apply the patch file to the codebase with timeout enforcement."""
        logger.info(f"Applying patch with {self.timeout_minutes}min timeout: {self.patch_file}")
        
        try:
            # Use git apply first
            result = subprocess.run(
                ['git', 'apply', '--verbose', self.patch_file],
                capture_output=True,
                text=True,
                timeout=self.timeout_minutes * 60,
                check=False
            )
            
            if result.returncode == 0:
                logger.info("Patch applied successfully with git apply")
                return True
            
            # Try with patch command as fallback
            logger.warning("Git apply failed, trying patch command...")
            result = subprocess.run(
                ['patch', '-p1', '-i', self.patch_file],
                capture_output=True,
                text=True,
                timeout=self.timeout_minutes * 60,
                check=False
            )
            
            if result.returncode == 0:
                logger.info("Patch applied successfully with patch command")
                return True
            else:
                logger.error(f"Both patch methods failed:")
                logger.error(f"  Git apply: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.error(f"Patch application timed out after {self.timeout_minutes} minutes")
            return False
        except Exception as e:
            logger.error(f"Error applying patch: {e}")
            return False
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """Load all benchmark tasks from YAML files."""
        tasks = []
        task_files = Path('tasks').glob('*.yaml')
        
        for task_file in task_files:
            if task_file.name == 'task_summary.json':
                continue
            
            try:
                with open(task_file, 'r') as f:
                    task = yaml.safe_load(f)
                    tasks.append(task)
            except Exception as e:
                logger.error(f"Error loading task {task_file}: {e}")
        
        logger.info(f"Loaded {len(tasks)} benchmark tasks")
        return tasks
    
    def calculate_weighted_score(self) -> float:
        """Calculate weighted overall score based on task difficulty."""
        if not self.results:
            return 0.0
        
        # Task weights from scoring rules (harder tasks worth more)
        task_weights = {
            'cross_file_reasoning': 1.0,   # baseline
            'refactor_rename': 1.2,        # requires precision
            'api_upgrade': 1.5,            # complex coordination  
            'bug_localization': 2.0        # highest difficulty
        }
        
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for result in self.results:
            # Extract task type from task_id (e.g., "cross_file_reasoning_01" -> "cross_file_reasoning")
            task_type = '_'.join(result.task_id.split('_')[:-1])
            weight = task_weights.get(task_type, 1.0)
            
            weighted_sum += result.score * weight
            weight_sum += weight
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0
    

    
    def restore_backup(self):
        """Restore from backup after validation (FIX: backup restore bug)."""
        if not self.backup_dir or not os.path.exists(self.backup_dir):
            logger.warning("No backup directory found to restore from")
            return
        
        logger.info(f"Restoring from backup: {self.backup_dir}")
        
        try:
            # Restore src directory
            if os.path.exists(os.path.join(self.backup_dir, 'src')):
                if os.path.exists('src'):
                    shutil.rmtree('src')
                shutil.copytree(os.path.join(self.backup_dir, 'src'), 'src')
                logger.info("Restored src directory")
            
            # Restore transforms directory
            if os.path.exists(os.path.join(self.backup_dir, 'transforms')):
                if os.path.exists('transforms'):
                    shutil.rmtree('transforms')
                shutil.copytree(os.path.join(self.backup_dir, 'transforms'), 'transforms')
                logger.info("Restored transforms directory")
            
            # Restore other backed up items
            for item in ['tasks', 'scoring']:
                backup_item = os.path.join(self.backup_dir, item)
                if os.path.exists(backup_item):
                    if os.path.exists(item):
                        if os.path.isfile(item):
                            os.remove(item)
                        else:
                            shutil.rmtree(item)
                    
                    if os.path.isfile(backup_item):
                        shutil.copy2(backup_item, item)
                    else:
                        shutil.copytree(backup_item, item)
            
            # Clean up temporary backup directory
            shutil.rmtree(self.backup_dir)
            self.backup_dir = None
            
            logger.info("Backup restored successfully")
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            logger.error(f"Manual cleanup may be needed for: {self.backup_dir}")


def main():
    """Main entry point for patch validation with REAL scoring."""
    parser = argparse.ArgumentParser(description='Validate and score a patch file using real scoring engine')
    parser.add_argument('patch_file', help='Path to the patch file to validate')
    parser.add_argument('--output', '-o', help='Output file for results (JSON)')
    parser.add_argument('--timeout', '-t', type=int, default=30, help='Timeout in minutes (default: 30)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.patch_file):
        logger.error(f"Patch file not found: {args.patch_file}")
        sys.exit(1)
    
    # Validate we're in the right directory
    if not os.path.exists('tasks') or not os.path.exists('src'):
        logger.error("Must run from benchmark corpus root directory (containing tasks/ and src/)")
        sys.exit(1)
    
    logger.info("🚀 Starting patch validation with REAL scoring engine!")
    
    validator = PatchValidator(args.patch_file, timeout_minutes=args.timeout)
    results = validator.validate_and_score()
    
    # Enhanced output with summary
    if 'overall_score' in results:
        print(f"\n📊 VALIDATION COMPLETE:")
        print(f"   Overall Score: {results['overall_score']:.3f}")
        print(f"   Execution Time: {results['execution_time']:.1f}s")
        print(f"   Patch Applied: {results.get('patch_applied', False)}")
        
        if results.get('task_results'):
            print(f"   Task Breakdown:")
            for task_result in results['task_results']:
                print(f"     • {task_result['task_id']}: {task_result['score']:.3f}")
    
    # Output detailed results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Detailed results saved to: {args.output}")
    else:
        print(f"\n📄 Detailed Results:")
        print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
