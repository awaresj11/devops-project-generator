#!/usr/bin/env python3
"""
Template management commands for DevOps Project Generator
"""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


def template(action: str, category: Optional[str] = None, name: Optional[str] = None, 
            output_dir: Optional[str] = None) -> None:
    """Manage and customize project templates"""
    try:
        if action == "list":
            _list_available_templates()
        elif action == "create":
            if not category or not name:
                console.print("[red]❌ --category and --name required for create action[/red]")
                console.print("[yellow]Usage: devops-project-generator template create --category <category> --name <template-name>[/yellow]")
                raise typer.Exit(1)
            _create_custom_template(category, name)
        elif action == "customize":
            if not category or not name:
                console.print("[red]❌ --category and --name required for customize action[/red]")
                console.print("[yellow]Usage: devops-project-generator template customize --category <category> --name <template-name>[/yellow]")
                raise typer.Exit(1)
            _customize_template(category, name)
        elif action == "export":
            if not output_dir:
                console.print("[red]❌ Output directory required for export action[/red]")
                console.print("[yellow]Usage: devops-project-generator template export --output <directory>[/yellow]")
                raise typer.Exit(1)
            _export_templates(output_dir)
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("[yellow]Available actions: list, create, customize, export[/yellow]")
            raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Template management error: {str(e)}")
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


def _list_available_templates() -> None:
    """List all available templates"""
    console.print(Panel.fit(
        "[bold blue]📋 Available Templates[/bold blue]\n"
        "[dim]Built-in templates for different DevOps configurations[/dim]",
        border_style="blue"
    ))
    
    template_categories = {
        "CI/CD": {
            "github-actions": "GitHub Actions workflows with multi-stage pipelines",
            "gitlab-ci": "GitLab CI/CD with auto-deployment",
            "jenkins": "Jenkins pipelines with Docker integration",
            "azure-pipelines": "Azure DevOps pipelines with YAML"
        },
        "Infrastructure": {
            "terraform": "Terraform modules for multi-cloud deployment",
            "cloudformation": "AWS CloudFormation templates",
            " pulumi": "Pulumi infrastructure as code",
            "ansible": "Ansible playbooks for configuration management"
        },
        "Deployment": {
            "kubernetes": "K8s manifests with Helm charts",
            "docker": "Docker containers with compose files",
            "serverless": "AWS Lambda and serverless functions",
            "static": "Static site deployment with CDN"
        },
        "Monitoring": {
            "prometheus": "Prometheus + Grafana monitoring stack",
            "datadog": "Datadog APM and monitoring",
            "elasticsearch": "ELK stack for logging and analytics",
            "cloudwatch": "AWS CloudWatch monitoring"
        },
        "Security": {
            "owasp": "OWASP security scanning and policies",
            "vault": "HashiCorp Vault secrets management",
            "cert-manager": "SSL certificate automation",
            "istio": "Service mesh security policies"
        }
    }
    
    for category, templates in template_categories.items():
        console.print(f"\n[bold]{category}:[/bold]")
        table = Table()
        table.add_column("Template", style="cyan")
        table.add_column("Description")
        
        for name, description in templates.items():
            table.add_row(name, description)
        
        console.print(table)


def _create_custom_template(category: str, name: str) -> None:
    """Create a new custom template"""
    import datetime
    
    console.print(f"[blue]📝 Creating custom template: {category}/{name}[/blue]")
    
    template_dir = Path.home() / ".devops-generator" / "templates" / category / name
    template_dir.mkdir(parents=True, exist_ok=True)
    
    # Create template structure
    subdirs = ["ci", "infra", "deploy", "monitoring", "security", "app"]
    for subdir in subdirs:
        (template_dir / subdir).mkdir(exist_ok=True)
    
    # Create template metadata
    import yaml
    metadata = {
        "name": name,
        "category": category,
        "version": "1.0.0",
        "description": f"Custom template: {category}/{name}",
        "author": "Custom User",
        "created": datetime.datetime.now().isoformat(),
        "components": {
            "ci": ["github-actions"],
            "infra": ["terraform"],
            "deploy": ["kubernetes"],
            "monitoring": ["prometheus"],
            "security": ["owasp"]
        },
        "variables": {
            "project_name": "string",
            "environment": "string",
            "cloud_provider": "string",
            "docker_registry": "string"
        }
    }
    
    metadata_file = template_dir / "template.yaml"
    with open(metadata_file, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, default_flow_style=False)
    
    # Create sample files
    sample_files = {
        "ci/github-actions.yml.j2": """# GitHub Actions Workflow for {{ project_name }}
name: {{ environment }}-pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run tests
      run: echo "Running tests for {{ project_name }}"
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to {{ environment }}
      run: echo "Deploying to {{ environment }}"

""",
        "infra/main.tf.j2": """# Terraform configuration for {{ project_name }}
provider "{{ cloud_provider }}" {
  region = var.region
}

variable "project_name" {
  description = "Project name"
  default = "{{ project_name }}"
}

variable "environment" {
  description = "Environment"
  default = "{{ environment }}"
}

# Add your infrastructure resources here
""",
        "deploy/k8s-deployment.yaml.j2": """# Kubernetes deployment for {{ project_name }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ project_name }}
  namespace: {{ environment }}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {{ project_name }}
  template:
    metadata:
      labels:
        app: {{ project_name }}
    spec:
      containers:
      - name: {{ project_name }}
        image: {{ docker_registry }}/{{ project_name }}:latest
        ports:
        - containerPort: 8080
"""
    }
    
    for file_path, content in sample_files.items():
        full_path = template_dir / file_path
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    console.print(f"[green]✅ Custom template created: {template_dir}[/green]")
    console.print("[yellow]💡 Edit the template files to customize your project structure[/yellow]")


def _customize_template(category: str, name: str) -> None:
    """Customize an existing template"""
    template_dir = Path.home() / ".devops-generator" / "templates" / category / name
    
    if not template_dir.exists():
        console.print(f"[red]❌ Template '{category}/{name}' not found[/red]")
        console.print(f"[yellow]Available templates in: {template_dir.parent.parent}[/yellow]")
        raise typer.Exit(1)
    
    console.print(f"[blue]🔧 Customizing template: {category}/{name}[/blue]")
    
    # Show template structure
    console.print(f"\n[dim]Template structure:[/dim]")
    for item in template_dir.rglob("*"):
        if item.is_file():
            relative_path = item.relative_to(template_dir)
            console.print(f"  📄 {relative_path}")
    
    console.print(f"\n[yellow]💡 Edit files in: {template_dir}[/yellow]")
    console.print("[dim]Use .j2 extension for Jinja2 templates[/dim]")


def _export_templates(output_dir: str) -> None:
    """Export built-in templates to a directory"""
    import shutil
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[blue]📤 Exporting templates to: {output_path}[/blue]")
    
    # Get the built-in templates directory
    builtin_templates = Path(__file__).parent.parent.parent.parent / "templates"
    
    if builtin_templates.exists():
        export_dir = output_path / "builtin-templates"
        shutil.copytree(builtin_templates, export_dir, dirs_exist_ok=True)
        console.print(f"[green]✅ Built-in templates exported to: {export_dir}[/green]")
    else:
        console.print("[yellow]⚠️  Built-in templates directory not found[/yellow]")
    
    # Export custom templates if they exist
    custom_templates_dir = Path.home() / ".devops-generator" / "templates"
    if custom_templates_dir.exists():
        custom_export_dir = output_path / "custom-templates"
        shutil.copytree(custom_templates_dir, custom_export_dir, dirs_exist_ok=True)
        console.print(f"[green]✅ Custom templates exported to: {custom_export_dir}[/green]")
