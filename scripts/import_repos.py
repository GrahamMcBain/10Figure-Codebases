#!/usr/bin/env python3
"""
Import source repositories into the benchmark corpus.

Clones the specified open-source repositories into src/ directory
using shallow history to keep size manageable.
"""

import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Repository configuration
REPOS = [
    {
        'name': 'kubernetes',
        'url': 'https://github.com/kubernetes/kubernetes',
        'folder': 'src/kubernetes/',
        'depth': 1  # Shallow clone
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


def validate_imports():
    """Validate that all repositories were successfully imported."""
    logger.info("Validating imported repositories...")
    
    for repo_config in REPOS:
        folder = repo_config['folder']
        name = repo_config['name']
        
        if not os.path.exists(folder):
            raise ValueError(f"Repository {name} not found at {folder}")
        
        if not os.listdir(folder):
            raise ValueError(f"Repository {name} folder is empty at {folder}")
        
        logger.info(f"✓ {name} imported successfully")


def main():
    """Main entry point for importing repositories."""
    logger.info("Starting repository import process...")
    
    # Ensure src directory exists
    os.makedirs('src', exist_ok=True)
    
    # Clone each repository
    for repo_config in REPOS:
        clone_repository(repo_config)
    
    # Validate all imports
    validate_imports()
    
    logger.info("Repository import completed successfully!")


if __name__ == '__main__':
    main()
