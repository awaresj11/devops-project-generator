#!/usr/bin/env python3
"""
Configuration management commands for DevOps Project Generator
"""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

logger = logging.getLogger(__name__)
console = Console()


def config(action: str, config_file: str = "devops-config.yaml") -> None:
    """Manage project configuration files"""
    config_path = Path(config_file)
    
    if action == "create":
        _create_config_file(config_path)
    elif action == "show":
        _show_config_file(config_path)
    elif action == "validate":
        _validate_config_file(config_path)
    else:
        console.print(f"[red]❌ Unknown action: {action}[/red]")
        console.print("[yellow]Available actions: create, show, validate[/yellow]")
        raise typer.Exit(1)


def _create_config_file(config_path: Path) -> None:
    """Create a sample configuration file"""
    console.print(f"[blue]📝 Creating configuration file: {config_path}[/blue]")
    
    sample_config = """# DevOps Project Generator Configuration
# This file defines the default settings for project generation

project:
  name: "my-devops-project"
  description: "A production-ready DevOps project"
  author: "Your Name"
  email: "your.email@example.com"

# CI/CD Configuration
ci:
  platform: "github-actions"  # github-actions, gitlab-ci, jenkins, none
  docker_registry: "docker.io"
  cache_dependencies: true

# Infrastructure Configuration  
infra:
  tool: "terraform"  # terraform, cloudformation, none
  cloud_provider: "aws"  # aws, gcp, azure
  region: "us-west-2"

# Deployment Configuration
deploy:
  method: "kubernetes"  # vm, docker, kubernetes
  environments: "dev,stage,prod"
  auto_scaling: true
  health_checks: true

# Observability Configuration
observability:
  level: "full"  # logs, logs-metrics, full
  metrics_retention: "30d"
  log_retention: "7d"
  alerting: true

# Security Configuration
security:
  level: "standard"  # basic, standard, strict
  ssl_certificates: true
  secrets_management: "vault"
  vulnerability_scanning: true

# Custom Templates (optional)
templates:
  custom_dir: "~/.devops-generator/templates"
  overwrite_defaults: false

# Advanced Options
advanced:
  multi_region: false
  blue_green_deployments: false
  canary_deployments: false
  disaster_recovery: false
"""
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(sample_config)
        console.print(f"[green]✅ Configuration file created: {config_path}[/green]")
        console.print("[yellow]💡 Edit this file to customize your project defaults[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error creating config file: {str(e)}[/red]")
        raise typer.Exit(1)


def _show_config_file(config_path: Path) -> None:
    """Display the current configuration file"""
    if not config_path.exists():
        console.print(f"[red]❌ Configuration file not found: {config_path}[/red]")
        console.print("[yellow]💡 Use 'devops-project-generator config create' to create one[/yellow]")
        raise typer.Exit(1)
    
    console.print(f"[blue]📋 Configuration file: {config_path}[/blue]")
    console.print()
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
            console.print(content)
    except Exception as e:
        console.print(f"[red]❌ Error reading config file: {str(e)}[/red]")
        raise typer.Exit(1)


def _validate_config_file(config_path: Path) -> None:
    """Validate the configuration file syntax and values"""
    if not config_path.exists():
        console.print(f"[red]❌ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[blue]🔍 Validating configuration file: {config_path}[/blue]")
    
    try:
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        # Validate structure
        required_sections = ["project", "ci", "deploy", "observability", "security"]
        missing_sections = []
        
        for section in required_sections:
            if section not in config_data:
                missing_sections.append(section)
        
        if missing_sections:
            console.print(f"[yellow]⚠️  Missing sections: {', '.join(missing_sections)}[/yellow]")
        
        # Validate values
        validation_errors = []
        
        if "ci" in config_data:
            ci_platform = config_data["ci"].get("platform", "")
            if ci_platform not in ["github-actions", "gitlab-ci", "jenkins", "none"]:
                validation_errors.append(f"Invalid CI platform: {ci_platform}")
        
        if "deploy" in config_data:
            deploy_method = config_data["deploy"].get("method", "")
            if deploy_method not in ["vm", "docker", "kubernetes"]:
                validation_errors.append(f"Invalid deployment method: {deploy_method}")
        
        if validation_errors:
            console.print("[red]❌ Validation errors found:[/red]")
            for error in validation_errors:
                console.print(f"  • {error}")
        else:
            console.print("[green]✅ Configuration file is valid![/green]")
    
    except ImportError:
        console.print("[yellow]⚠️  PyYAML not installed, cannot validate YAML syntax[/yellow]")
        console.print("[dim]Install with: pip install PyYAML[/dim]")
    except yaml.YAMLError as e:
        console.print(f"[red]❌ YAML syntax error: {str(e)}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error validating config: {str(e)}[/red]")
        raise typer.Exit(1)
