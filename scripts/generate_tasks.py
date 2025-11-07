#!/usr/bin/env python3
"""
Generate benchmark tasks and ground truth data for evaluation.

Creates YAML task definitions and corresponding JSON ground truth files
for different types of coding benchmarks.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TaskGenerator:
    """Generates benchmark tasks and ground truth data."""
    
    def __init__(self):
        self.tasks = []
        self.ground_truth = {}
    
    def generate_all_tasks(self):
        """Generate all types of benchmark tasks."""
        logger.info("Generating benchmark tasks...")
        
        self.generate_cross_file_reasoning_tasks()
        self.generate_refactor_rename_tasks()
        self.generate_api_upgrade_tasks()
        self.generate_bug_localization_tasks()
        
        self.save_tasks_and_ground_truth()
        logger.info("Task generation completed!")
    
    def generate_cross_file_reasoning_tasks(self):
        """Generate cross-file reasoning benchmark tasks."""
        logger.info("Generating cross-file reasoning tasks...")
        
        # Load wrapper layers from transforms
        wrapper_layers = self._load_transform_data('transforms/wrapper_layers.json')
        
        task = {
            'task_id': 'cross_file_reasoning_01',
            'type': 'cross_file_reasoning',
            'start_symbol': 'FooMethod',
            'goal': 'Find implementation and summarize call path',
            'ground_truth': 'scoring/oracle/expected_symbol_paths.json',
            'description': 'Trace a function call through multiple wrapper layers to find the actual implementation',
            'max_time_minutes': 10,
            'difficulty': 'medium'
        }
        
        ground_truth = {
            'task_id': 'cross_file_reasoning_01',
            'expected_call_path': [
                'src/kubernetes/pkg/api/handler.go:ProcessRequest',
                'src/kubernetes/pkg/interfaces/processor.go:IProcessor.Process',
                'src/kubernetes/pkg/wrappers/logging.go:LoggingWrapper.Process',
                'src/kubernetes/pkg/impl/processor_impl.go:ProcessorImpl.ProcessInternal'
            ],
            'expected_implementation_file': 'src/kubernetes/pkg/impl/processor_impl.go',
            'expected_line_range': [45, 67]
        }
        
        self.tasks.append(task)
        self.ground_truth['cross_file_reasoning_01'] = ground_truth
    
    def generate_refactor_rename_tasks(self):
        """Generate refactor/rename benchmark tasks."""
        logger.info("Generating refactor rename tasks...")
        
        # Load renames from transforms
        renames = self._load_transform_data('transforms/renames.json')
        
        task = {
            'task_id': 'refactor_rename_01',
            'type': 'refactor_rename', 
            'symbol_to_rename': 'ProcessRequest',
            'new_name': 'HandleRequest',
            'goal': 'Rename function and update all references',
            'ground_truth': 'scoring/oracle/expected_refactor_targets.json',
            'description': 'Rename a function that appears in multiple files and update all call sites',
            'max_time_minutes': 15,
            'difficulty': 'hard'
        }
        
        ground_truth = {
            'task_id': 'refactor_rename_01',
            'files_to_modify': [
                'src/kubernetes/pkg/api/handler.go',
                'src/django/core/views.py',
                'src/tensorflow/core/framework/processor.h'
            ],
            'expected_changes': [
                {
                    'file': 'src/kubernetes/pkg/api/handler.go',
                    'line': 23,
                    'old': 'func ProcessRequest(',
                    'new': 'func HandleRequest('
                },
                {
                    'file': 'src/django/core/views.py', 
                    'line': 156,
                    'old': 'result = ProcessRequest(data)',
                    'new': 'result = HandleRequest(data)'
                }
            ]
        }
        
        self.tasks.append(task)
        self.ground_truth['refactor_rename_01'] = ground_truth
    
    def generate_api_upgrade_tasks(self):
        """Generate API upgrade benchmark tasks."""
        logger.info("Generating API upgrade tasks...")
        
        # Load API migrations from transforms
        api_migrations = self._load_transform_data('transforms/api_migrations.json')
        
        task = {
            'task_id': 'api_upgrade_01',
            'type': 'api_upgrade',
            'description': 'Upgrade FooMethod v1 calls to v2 API across repository',
            'old_api': 'FooMethod(param1, param2)',
            'new_api': 'FooMethodV2(param1, param2, options={})',
            'goal': 'Update all v1 API calls to use v2 signature',
            'ground_truth': 'scoring/oracle/expected_api_migration_results.json',
            'max_time_minutes': 20,
            'difficulty': 'hard'
        }
        
        ground_truth = {
            'task_id': 'api_upgrade_01',
            'total_callsites': 15,
            'expected_upgrades': 12,  # Not all need to be upgraded per requirements
            'callsites': [
                {
                    'file': 'src/kubernetes/pkg/client/client.go',
                    'line': 89,
                    'needs_upgrade': True,
                    'old_call': 'FooMethod(req, ctx)',
                    'new_call': 'FooMethodV2(req, ctx, options={})'
                },
                {
                    'file': 'src/django/utils/helpers.py',
                    'line': 234,
                    'needs_upgrade': False,  # Some remain v1 to simulate drift
                    'reason': 'Legacy compatibility required'
                }
            ]
        }
        
        self.tasks.append(task)
        self.ground_truth['api_upgrade_01'] = ground_truth
    
    def generate_bug_localization_tasks(self):
        """Generate bug localization benchmark tasks.""" 
        logger.info("Generating bug localization tasks...")
        
        task = {
            'task_id': 'bug_localization_01',
            'type': 'bug_localization',
            'description': 'Find the source of a null pointer exception in request processing',
            'error_message': 'NullPointerException at RequestProcessor.process()',
            'symptoms': [
                'Server crashes when processing certain API requests',
                'Error occurs only with requests containing empty headers',
                'Stack trace points to RequestProcessor module'
            ],
            'goal': 'Identify the exact file and line causing the bug',
            'ground_truth': 'scoring/oracle/expected_bug_locations.json',
            'max_time_minutes': 25,
            'difficulty': 'expert'
        }
        
        ground_truth = {
            'task_id': 'bug_localization_01',
            'bug_location': {
                'file': 'src/kubernetes/pkg/api/request_processor.go',
                'line_range': [156, 158],
                'root_cause': 'Missing null check on headers map before accessing',
                'fix_description': 'Add null check: if headers == nil { headers = make(map[string]string) }'
            },
            'related_files': [
                'src/kubernetes/pkg/api/handler.go',
                'src/kubernetes/pkg/validation/request_validator.go'
            ]
        }
        
        self.tasks.append(task)
        self.ground_truth['bug_localization_01'] = ground_truth
    
    def _load_transform_data(self, filepath: str) -> Dict[str, Any]:
        """Load transformation data from JSON file."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Transform file not found: {filepath}")
            return {}
    
    def save_tasks_and_ground_truth(self):
        """Save task definitions and ground truth data."""
        logger.info("Saving tasks and ground truth data...")
        
        # Ensure directories exist
        os.makedirs('tasks', exist_ok=True)
        os.makedirs('scoring/oracle', exist_ok=True)
        
        # Save individual task YAML files
        for task in self.tasks:
            task_file = f"tasks/{task['task_id']}.yaml"
            with open(task_file, 'w') as f:
                yaml.dump(task, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved task: {task_file}")
        
        # Save ground truth JSON files
        for task_id, truth_data in self.ground_truth.items():
            if 'cross_file' in task_id:
                truth_file = 'scoring/oracle/expected_symbol_paths.json'
            elif 'refactor' in task_id:
                truth_file = 'scoring/oracle/expected_refactor_targets.json'
            elif 'api_upgrade' in task_id:
                truth_file = 'scoring/oracle/expected_api_migration_results.json'
            elif 'bug_localization' in task_id:
                truth_file = 'scoring/oracle/expected_bug_locations.json'
            else:
                truth_file = f'scoring/oracle/{task_id}.json'
            
            with open(truth_file, 'w') as f:
                json.dump(truth_data, f, indent=2)
            logger.info(f"Saved ground truth: {truth_file}")
        
        # Save summary file
        summary = {
            'total_tasks': len(self.tasks),
            'task_types': list(set(task['type'] for task in self.tasks)),
            'tasks': [{'id': task['task_id'], 'type': task['type']} for task in self.tasks]
        }
        
        with open('tasks/task_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Generated {len(self.tasks)} benchmark tasks")


def main():
    """Main entry point for task generation."""
    generator = TaskGenerator()
    generator.generate_all_tasks()


if __name__ == '__main__':
    main()
