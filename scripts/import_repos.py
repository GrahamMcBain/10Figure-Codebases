#!/usr/bin/env python3
"""
Import source repositories into the benchmark corpus.

Clones the specified open-source repositories into src/ directory
using shallow history to keep size manageable.
"""

import os
import argparse
import subprocess
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_repository_config(core_only: bool = False) -> List[Dict[str, Any]]:
    """Load repository configuration from repos.yaml."""
    try:
        with open('repos.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        if core_only:
            repos = config.get('core_repos', [])
        else:
            repos = config.get('core_repos', []) + config.get('extended_repos', [])
        
        # Convert to expected format
        formatted_repos = []
        for repo in repos:
            formatted_repos.append({
                'name': repo['name'],
                'url': repo['url'],
                'folder': f"src/{repo['name']}/",
                'depth': repo.get('depth', 1)
            })
        
        return formatted_repos
        
    except FileNotFoundError:
        # Fallback to original hardcoded repos
        logger.warning("repos.yaml not found, using fallback configuration")
        return [
            {
                'name': 'kubernetes',
                'url': 'https://github.com/kubernetes/kubernetes',
                'folder': 'src/kubernetes/',
                'depth': 1
            },
            {
                'name': 'envoy',
                'url': 'https://github.com/envoyproxy/envoy',
                'folder': 'src/envoy/',
                'depth': 1
            },
            {
                'name': 'django',
                'url': 'https://github.com/django/django',
                'folder': 'src/django/',
                'depth': 1
            },
            {
                'name': 'tensorflow',
                'url': 'https://github.com/tensorflow/tensorflow',
                'folder': 'src/tensorflow/',
                'depth': 1
            }
        ]


def clone_repository(repo_config):
    """Clone a single repository with shallow history."""
    name = repo_config['name']
    url = repo_config['url']
    folder = repo_config['folder']
    depth = repo_config['depth']
    
    logger.info(f"Cloning {name} from {url}")
    
    # Create target directory if it doesn't exist
    Path(folder).mkdir(parents=True, exist_ok=True)
    
    # Remove existing directory if present
    if os.path.exists(folder) and os.listdir(folder):
        logger.info(f"Removing existing {folder}")
        subprocess.run(['rm', '-rf', folder], check=True)
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    # Clone with shallow history
    try:
        cmd = ['git', 'clone', '--depth', str(depth), url, folder]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Successfully cloned {name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone {name}: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise


def validate_imports(repos):
    """Validate that all repositories were successfully imported."""
    logger.info("Validating imported repositories...")
    
    for repo_config in repos:
        folder = repo_config['folder']
        name = repo_config['name']
        
        if not os.path.exists(folder):
            raise ValueError(f"Repository {name} not found at {folder}")
        
        if not os.listdir(folder):
            raise ValueError(f"Repository {name} folder is empty at {folder}")
        
        logger.info(f"✓ {name} imported successfully")


def main():
    """Main entry point for importing repositories."""
    parser = argparse.ArgumentParser(description='Import source repositories for benchmark corpus')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for deterministic results')
    parser.add_argument('--core-only', action='store_true', help='Import only core repositories (for CI)')
    
    args = parser.parse_args()
    
    # Set environment for deterministic execution
    os.environ['PYTHONHASHSEED'] = '0'
    
    logger.info("Starting repository import process...")
    
    # Load repository configuration
    repos = load_repository_config(core_only=args.core_only)
    
    if args.core_only:
        logger.info(f"Importing {len(repos)} core repositories for CI")
    else:
        logger.info(f"Importing {len(repos)} repositories for full corpus")
    
    # Ensure src directory exists
    os.makedirs('src', exist_ok=True)
    
    # Clone each repository
    for repo_config in repos:
        clone_repository(repo_config)
    
    # Validate all imports
    validate_imports(repos)
    
    logger.info("Repository import completed successfully!")


if __name__ == '__main__':
    main()
