#!/usr/bin/env python3
"""
Commands package initialization for DevOps Project Generator CLI
"""

# Import all command modules to make them available
from .project import validate, info, health, cleanup
from .config import config
from .template import template
from .backup import backup
from .profile import profile
from .test import test
from .scan import scan
from .multi_env import multi_env

__all__ = [
    # Project commands
    'validate',
    'info', 
    'health',
    'cleanup',
    
    # Configuration commands
    'config',
    
    # Template commands
    'template',
    
    # Backup commands
    'backup',
    
    # Profile commands
    'profile',
    
    # Testing commands
    'test',
    
    # Scanning commands
    'scan',
    
    # Multi-environment commands
    'multi_env',
]
