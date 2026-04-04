#!/usr/bin/env python3
"""
CLI interface for DevOps Project Generator
"""

import os
import sys
import logging
import time
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

import typer
from rich.console import Console
from rich.panel import Panel
from rich.traceback import install

from generator import ProjectConfig, DevOpsProjectGenerator
from .utils import (
    format_duration, format_file_size, calculate_project_stats,
    show_success_message, show_error_message, show_warning_message,
    show_progress_spinner, safe_execute, validate_project_name,
    validate_output_path, safe_print
)
from .commands import (
    ProjectCommands, ConfigCommands, TemplateCommands,
    BackupCommands, ProfileCommands, TestCommands,
    ScanCommands, MultiEnvCommands
)

# Install rich traceback for better error display
install(show_locals=True)

# Configure logging with better formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('devops-generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)



# =============================================================================
# MAIN CLI APPLICATION
# =============================================================================

app = typer.Typer(
    name="devops-project-generator",
    help="🚀 DevOps Project Generator - Scaffold production-ready DevOps repositories",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()


@contextmanager
def handle_cli_errors():
    """Context manager for consistent CLI error handling"""
    try:
        yield
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
        logger.info("Operation cancelled by user")
        raise typer.Exit(130)
    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"CLI error: {str(e)}", exc_info=True)
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        console.print("[yellow]💡 Check the log file for details: devops-generator.log[/yellow]")
        raise typer.Exit(1)


@app.command()
def init(
    pipeline: Optional[str] = typer.Option(
        None,
        "--pipeline",
        help="Pipeline framework: nodejs-typescript, python, java-maven, go, docker-multistage, terraform-module, kubernetes-operator, microservice",
        show_choices=True,
    ),
    ci: Optional[str] = typer.Option(
        None,
        "--ci",
        help="CI/CD platform: github-actions, gitlab-ci, jenkins, azure-pipelines, gitlab-runners, none",
        show_choices=True,
    ),
    infra: Optional[str] = typer.Option(
        None,
        "--infra",
        help="Infrastructure pattern: aws-vpc-eks, azure-vnet-aks, gcp-vpc-gke, multicloud-terraform, kubernetes-onprem, aws-ecs-fargate, ansible-automation",
        show_choices=True,
    ),
    deploy: Optional[str] = typer.Option(
        None,
        "--deploy",
        help="Deployment strategy: blue-green, canary, rolling, gitops-argocd, helm-charts, kustomize, serverless-lambda",
        show_choices=True,
    ),
    envs: Optional[str] = typer.Option(
        None,
        "--envs",
        help="Environments: single, dev,stage,prod",
    ),
    observability: Optional[str] = typer.Option(
        None,
        "--observability",
        help="Observability stack: prometheus-grafana, elk-stack, datadog, jaeger-prometheus, cloudwatch, new-relic",
        show_choices=True,
    ),
    security: Optional[str] = typer.Option(
        None,
        "--security",
        help="Security framework: nist-csf, cis-benchmarks, zero-trust, soc2, gdpr, hipaa",
        show_choices=True,
    ),
    project_name: Optional[str] = typer.Option(
        "devops-project",
        "--name",
        help="Project name",
        callback=lambda ctx, param, value: validate_project_name(value) if value else value,
    ),
    output_dir: Optional[str] = typer.Option(
        ".",
        "--output",
        help="Output directory",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive/--no-interactive",
        help="Interactive mode",
    ),
) -> None:
    """Initialize a new DevOps project"""
    try:
        # Validate output path
        try:
            output_path = validate_output_path(output_dir)
        except typer.BadParameter as e:
            console.print(f"[red]❌ {str(e)}[/red]")
            raise typer.Exit(1)
        
        # Display welcome message
        console.print(Panel.fit(
            "[bold blue]🚀 DevOps Project Generator[/bold blue]\n"
            "[dim]Scaffold production-ready DevOps repositories[/dim]",
            border_style="blue"
        ))
        
        logger.info(f"Starting project generation: {project_name}")
        
        # Get configuration
        try:
            if interactive:
                config = _interactive_mode()
            else:
                config = ProjectConfig(
                    pipeline=pipeline,
                    ci=ci,
                    infra=infra,
                    deploy=deploy,
                    envs=envs,
                    observability=observability,
                    security=security,
                    project_name=project_name,
                )
        except Exception as e:
            logger.error(f"Configuration error: {str(e)}")
            console.print(f"[red]❌ Configuration error: {str(e)}[/red]")
            raise typer.Exit(1)
        
        # Validate configuration
        if not config.validate():
            console.print("[red]❌ Invalid configuration. Please check your options.[/red]")
            console.print("[yellow]💡 Use 'devops-project-generator list-options' to see valid choices[/yellow]")
            logger.error("Invalid configuration provided")
            raise typer.Exit(1)
        
        # Check if project directory already exists
        project_path = output_path / config.project_name
        if project_path.exists():
            console.print(f"[yellow]⚠️  Directory '{config.project_name}' already exists.[/yellow]")
            if not typer.confirm("Continue and overwrite?"):
                console.print("[dim]Operation cancelled.[/dim]")
                logger.info("Operation cancelled by user due to existing directory")
                raise typer.Exit(0)
            
            try:
                shutil.rmtree(project_path)
                logger.info(f"Removed existing directory: {project_path}")
            except PermissionError:
                console.print(f"[red]❌ Permission denied when removing existing directory[/red]")
                console.print(f"[yellow]💡 Try removing {project_path} manually[/yellow]")
                raise typer.Exit(1)
            except Exception as e:
                console.print(f"[red]❌ Error removing existing directory: {str(e)}[/red]")
                logger.error(f"Error removing directory: {str(e)}")
                raise typer.Exit(1)
        
        # Generate project
        try:
            start_time = time.time()
            with show_progress_spinner("Generating DevOps project...") as progress:
                task = progress.add_task("Initializing...", total=None)
                
                generator = DevOpsProjectGenerator(config, str(output_path))
                generator.generate()
            
            generation_time = time.time() - start_time
            
            # Calculate project statistics
            project_stats = _calculate_project_stats(project_path)
            
            # Display success message with statistics
            success_msg = (
                f"Generated {project_stats['files']} files across {project_stats['directories']} directories\n"
                f"Project size: {project_stats['size_formatted']}\n"
                f"Generation time: {format_duration(generation_time)}"
            )
            show_success_message("Project Generated Successfully!", success_msg)
            
            console.print(f"\n[bold]📍 Project location:[/bold] {project_path}")
            console.print("\n[bold]🚀 Next steps:[/bold]")
            console.print(f"  cd {config.project_name}")
            console.print("  make help")
            
            logger.info(f"Project generated successfully: {project_path}")
            
        except KeyboardInterrupt:
            show_warning_message("Generation Cancelled", "Project generation was cancelled by user")
            logger.info("Generation cancelled by user")
            # Clean up partial project if it exists
            if project_path.exists():
                try:
                    shutil.rmtree(project_path)
                    logger.info("Cleaned up partial project")
                except Exception:
                    pass
            raise typer.Exit(130)
        except Exception as e:
            logger.error(f"Error generating project: {str(e)}", exc_info=True)
            show_error_message("Generation Failed", f"Failed to generate project: {str(e)}")
            console.print("[yellow]💡 Check the log file for details: devops-generator.log[/yellow]")
            
            # Clean up partial project if it exists
            if project_path.exists():
                try:
                    shutil.rmtree(project_path)
                    logger.info("Cleaned up partial project due to error")
                except Exception:
                    pass
            raise typer.Exit(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
        logger.info("Operation cancelled by user")
        raise typer.Exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        console.print(f"\n[red]❌ Unexpected error: {str(e)}[/red]")
        console.print("[yellow]💡 Check the log file for details: devops-generator.log[/yellow]")
        raise typer.Exit(1)


def _interactive_mode() -> ProjectConfig:
    """Interactive configuration mode"""
    console.print("\n[bold]🔧 Interactive Configuration[/bold]\n")
    
    # Pipeline framework selection
    pipeline_table = Table(title="Pipeline Frameworks")
    pipeline_table.add_column("Option", style="cyan")
    pipeline_table.add_column("Description")
    pipeline_table.add_row("nodejs-typescript", "Node.js + TypeScript pipelines")
    pipeline_table.add_row("python", "Python application pipelines")
    pipeline_table.add_row("java-maven", "Enterprise Java pipelines")
    pipeline_table.add_row("go", "Go application pipelines")
    pipeline_table.add_row("docker-multistage", "Containerized application pipelines")
    pipeline_table.add_row("terraform-module", "Infrastructure module pipelines")
    pipeline_table.add_row("kubernetes-operator", "Kubernetes operator pipelines")
    pipeline_table.add_row("microservice", "Microservice architecture pipelines")
    console.print(pipeline_table)
    
    while True:
        pipeline = typer.prompt("Choose pipeline framework", type=str).lower()
        if pipeline in ProjectConfig.VALID_PIPELINE_OPTIONS:
            break
        console.print(f"[red]Invalid option. Please choose from: {', '.join(ProjectConfig.VALID_PIPELINE_OPTIONS)}[/red]")
    
    # CI/CD selection
    ci_table = Table(title="CI/CD Platforms")
    ci_table.add_column("Option", style="cyan")
    ci_table.add_column("Description")
    ci_table.add_row("github-actions", "GitHub Actions workflows")
    ci_table.add_row("gitlab-ci", "GitLab CI/CD pipelines")
    ci_table.add_row("jenkins", "Jenkins pipeline files")
    ci_table.add_row("azure-pipelines", "Azure DevOps pipelines")
    ci_table.add_row("gitlab-runners", "GitLab Runners")
    ci_table.add_row("none", "No CI/CD")
    console.print(ci_table)
    
    while True:
        ci = typer.prompt("Choose CI/CD platform", type=str).lower()
        if ci in ProjectConfig.VALID_CI_OPTIONS:
            break
        console.print(f"[red]Invalid option. Please choose from: {', '.join(ProjectConfig.VALID_CI_OPTIONS)}[/red]")
    
    # Infrastructure selection
    infra_table = Table(title="Infrastructure Patterns")
    infra_table.add_column("Option", style="cyan")
    infra_table.add_column("Description")
    infra_table.add_row("aws-vpc-eks", "Amazon EKS with VPC networking")
    infra_table.add_row("azure-vnet-aks", "Azure AKS with virtual networking")
    infra_table.add_row("gcp-vpc-gke", "Google GKE with VPC networking")
    infra_table.add_row("multicloud-terraform", "Cross-cloud infrastructure")
    infra_table.add_row("kubernetes-onprem", "On-premises Kubernetes")
    infra_table.add_row("aws-ecs-fargate", "Serverless container orchestration")
    infra_table.add_row("ansible-automation", "Configuration management")
    console.print(infra_table)
    
    while True:
        infra = typer.prompt("Choose infrastructure pattern", type=str).lower()
        if infra in ProjectConfig.VALID_INFRA_OPTIONS:
            break
        console.print(f"[red]Invalid option. Please choose from: {', '.join(ProjectConfig.VALID_INFRA_OPTIONS)}[/red]")
    
    # Deployment selection
    deploy_table = Table(title="Deployment Strategies")
    deploy_table.add_column("Option", style="cyan")
    deploy_table.add_column("Description")
    deploy_table.add_row("blue-green", "Zero-downtime deployments")
    deploy_table.add_row("canary", "Gradual rollout deployments")
    deploy_table.add_row("rolling", "Incremental updates")
    deploy_table.add_row("gitops-argocd", "Git-based continuous deployment")
    deploy_table.add_row("helm-charts", "Kubernetes package management")
    deploy_table.add_row("kustomize", "Kubernetes configuration management")
    deploy_table.add_row("serverless-lambda", "AWS Lambda deployments")
    console.print(deploy_table)
    
    while True:
        deploy = typer.prompt("Choose deployment strategy", type=str).lower()
        if deploy in ProjectConfig.VALID_DEPLOY_OPTIONS:
            break
        console.print(f"[red]Invalid option. Please choose from: {', '.join(ProjectConfig.VALID_DEPLOY_OPTIONS)}[/red]")
    
    # Environments
    while True:
        envs = typer.prompt("Choose environments (single, dev,stage,prod)", type=str).lower()
        if envs in ["single", "dev", "stage", "prod"] or "," in envs:
            break
        console.print("[red]Invalid environment format. Use 'single' or comma-separated values like 'dev,stage,prod'[/red]")
    
    # Observability
    obs_table = Table(title="Observability Stacks")
    obs_table.add_column("Option", style="cyan")
    obs_table.add_column("Description")
    obs_table.add_row("prometheus-grafana", "Metrics and visualization")
    obs_table.add_row("elk-stack", "Elasticsearch, Logstash, Kibana")
    obs_table.add_row("datadog", "Full-stack monitoring")
    obs_table.add_row("jaeger-prometheus", "Distributed tracing and metrics")
    obs_table.add_row("cloudwatch", "AWS native monitoring")
    obs_table.add_row("new-relic", "Application performance monitoring")
    console.print(obs_table)
    
    while True:
        observability = typer.prompt("Choose observability stack", type=str).lower()
        if observability in ProjectConfig.VALID_OBS_OPTIONS:
            break
        console.print(f"[red]Invalid option. Please choose from: {', '.join(ProjectConfig.VALID_OBS_OPTIONS)}[/red]")
    
    # Security
    sec_table = Table(title="Security Frameworks")
    sec_table.add_column("Option", style="cyan")
    sec_table.add_column("Description")
    sec_table.add_row("nist-csf", "NIST Cybersecurity Framework")
    sec_table.add_row("cis-benchmarks", "Center for Internet Security controls")
    sec_table.add_row("zero-trust", "Zero Trust Architecture")
    sec_table.add_row("soc2", "Service Organization Control 2")
    sec_table.add_row("gdpr", "General Data Protection Regulation")
    sec_table.add_row("hipaa", "Health Insurance Portability and Accountability Act")
    console.print(sec_table)
    
    while True:
        security = typer.prompt("Choose security framework", type=str).lower()
        if security in ProjectConfig.VALID_SEC_OPTIONS:
            break
        console.print(f"[red]Invalid option. Please choose from: {', '.join(ProjectConfig.VALID_SEC_OPTIONS)}[/red]")
    
    project_name = typer.prompt("Project name", default="devops-project")
    
    return ProjectConfig(
        pipeline=pipeline,
        ci=ci,
        infra=infra,
        deploy=deploy,
        envs=envs,
        observability=observability,
        security=security,
        project_name=project_name,
    )


@app.command()
def list_options() -> None:
    """List all available options"""
    console.print(Panel.fit(
        "[bold blue]📋 Available Options[/bold blue]",
        border_style="blue"
    ))
    
    # Pipeline Framework Options
    console.print("\n[bold]🔄 Pipeline Frameworks:[/bold]")
    pipeline_table = Table()
    pipeline_table.add_column("Option", style="cyan")
    pipeline_table.add_column("Description")
    pipeline_table.add_row("nodejs-typescript", "Node.js + TypeScript pipelines")
    pipeline_table.add_row("python", "Python application pipelines")
    pipeline_table.add_row("java-maven", "Enterprise Java pipelines")
    pipeline_table.add_row("go", "Go application pipelines")
    pipeline_table.add_row("docker-multistage", "Containerized application pipelines")
    pipeline_table.add_row("terraform-module", "Infrastructure module pipelines")
    pipeline_table.add_row("kubernetes-operator", "Kubernetes operator pipelines")
    pipeline_table.add_row("microservice", "Microservice architecture pipelines")
    console.print(pipeline_table)
    
    # CI/CD Options
    console.print("\n[bold]🔄 CI/CD Platforms:[/bold]")
    ci_table = Table()
    ci_table.add_column("Option", style="cyan")
    ci_table.add_column("Description")
    ci_table.add_row("github-actions", "GitHub Actions workflows")
    ci_table.add_row("gitlab-ci", "GitLab CI/CD pipelines")
    ci_table.add_row("jenkins", "Jenkins pipeline files")
    ci_table.add_row("azure-pipelines", "Azure DevOps pipelines")
    ci_table.add_row("gitlab-runners", "GitLab Runners")
    ci_table.add_row("none", "No CI/CD")
    console.print(ci_table)
    
    # Infrastructure Options
    console.print("\n[bold]☁️ Infrastructure Patterns:[/bold]")
    infra_table = Table()
    infra_table.add_column("Option", style="cyan")
    infra_table.add_column("Description")
    infra_table.add_row("aws-vpc-eks", "Amazon EKS with VPC networking")
    infra_table.add_row("azure-vnet-aks", "Azure AKS with virtual networking")
    infra_table.add_row("gcp-vpc-gke", "Google GKE with VPC networking")
    infra_table.add_row("multicloud-terraform", "Cross-cloud infrastructure")
    infra_table.add_row("kubernetes-onprem", "On-premises Kubernetes")
    infra_table.add_row("aws-ecs-fargate", "Serverless container orchestration")
    infra_table.add_row("ansible-automation", "Configuration management")
    console.print(infra_table)
    
    # Deployment Options
    console.print("\n[bold]🚀 Deployment Strategies:[/bold]")
    deploy_table = Table()
    deploy_table.add_column("Option", style="cyan")
    deploy_table.add_column("Description")
    deploy_table.add_row("blue-green", "Zero-downtime deployments")
    deploy_table.add_row("canary", "Gradual rollout deployments")
    deploy_table.add_row("rolling", "Incremental updates")
    deploy_table.add_row("gitops-argocd", "Git-based continuous deployment")
    deploy_table.add_row("helm-charts", "Kubernetes package management")
    deploy_table.add_row("kustomize", "Kubernetes configuration management")
    deploy_table.add_row("serverless-lambda", "AWS Lambda deployments")
    console.print(deploy_table)
    
    # Environment Options
    console.print("\n[bold]🌍 Environment Options:[/bold]")
    env_table = Table()
    env_table.add_column("Option", style="cyan")
    env_table.add_column("Description")
    env_table.add_row("single", "Single environment")
    env_table.add_row("dev", "Development environment")
    env_table.add_row("dev,stage,prod", "Multi-environment setup")
    console.print(env_table)
    
    # Observability Options
    console.print("\n[bold]📊 Observability Stacks:[/bold]")
    obs_table = Table()
    obs_table.add_column("Option", style="cyan")
    obs_table.add_column("Description")
    obs_table.add_row("prometheus-grafana", "Metrics and visualization")
    obs_table.add_row("elk-stack", "Elasticsearch, Logstash, Kibana")
    obs_table.add_row("datadog", "Full-stack monitoring")
    obs_table.add_row("jaeger-prometheus", "Distributed tracing and metrics")
    obs_table.add_row("cloudwatch", "AWS native monitoring")
    obs_table.add_row("new-relic", "Application performance monitoring")
    console.print(obs_table)
    
    # Security Options
    console.print("\n[bold]🔒 Security Frameworks:[/bold]")
    sec_table = Table()
    sec_table.add_column("Option", style="cyan")
    sec_table.add_column("Description")
    sec_table.add_row("nist-csf", "NIST Cybersecurity Framework")
    sec_table.add_row("cis-benchmarks", "Center for Internet Security controls")
    sec_table.add_row("zero-trust", "Zero Trust Architecture")
    sec_table.add_row("soc2", "Service Organization Control 2")
    sec_table.add_row("gdpr", "General Data Protection Regulation")
    sec_table.add_row("hipaa", "Health Insurance Portability and Accountability Act")
    console.print(sec_table)




@app.command()
def validate(
    project_path: str = typer.Argument(
        ".",
        help="Path to the DevOps project to validate"
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Automatically fix common issues"
    ),
) -> None:
    """Validate a DevOps project structure and configuration"""
    with handle_cli_errors():
        ProjectCommands.validate(project_path, fix)


@app.command()
def info(
    project_path: str = typer.Argument(
        ".",
        help="Path to the DevOps project to analyze"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        help="Show detailed file-by-file analysis"
    ),
) -> None:
    """Show detailed information and statistics about a DevOps project"""
    with handle_cli_errors():
        ProjectCommands.info(project_path, detailed)


@app.command()
def health(
    project_path: str = typer.Argument(
        ".",
        help="Path to the DevOps project to check"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        help="Show detailed health analysis"
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Attempt to fix health issues automatically"
    ),
) -> None:
    """Perform comprehensive health check on DevOps project"""
    with handle_cli_errors():
        ProjectCommands.health(project_path, detailed, fix)


@app.command()
def cleanup(
    project_path: str = typer.Argument(
        ".",
        help="Path to the DevOps project to cleanup"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation prompts"
    ),
    keep_config: bool = typer.Option(
        False,
        "--keep-config",
        help="Keep configuration files"
    ),
) -> None:
    """Clean up a DevOps project and remove generated resources"""
    with handle_cli_errors():
        ProjectCommands.cleanup(project_path, force, keep_config)


@app.command()
def config(
    action: str = typer.Argument(
        "create",
        help="Action: create, show, or validate"
    ),
    config_file: Optional[str] = typer.Option(
        "devops-config.yaml",
        "--file",
        help="Configuration file path"
    ),
) -> None:
    """Manage project configuration files"""
    with handle_cli_errors():
        ConfigCommands.config(action, config_file)


@app.command()
def test(
    project_path: str = typer.Argument(..., help="Path to project to test"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
) -> None:
    """Run integration tests on generated project"""
    with handle_cli_errors():
        TestCommands.test(project_path, verbose)


@app.command()
def scan(
    project_path: str = typer.Argument(
        ".",
        help="Path to project to scan for dependencies"
    ),
    export: Optional[str] = typer.Option(
        None,
        "--export",
        help="Export report to file (e.g., report.json, report.yaml)"
    ),
    format: str = typer.Option(
        "json",
        "--format",
        help="Export format: json or yaml"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        help="Show detailed dependency information"
    )
) -> None:
    """Scan project dependencies and security vulnerabilities"""
    with handle_cli_errors():
        ScanCommands.scan(project_path, export, format, detailed)


@app.command()
def multi_env(
    project_path: str = typer.Argument(
        ".",
        help="Path to project for multi-environment configuration"
    ),
    environments: str = typer.Option(
        "dev,stage,prod",
        "--envs",
        help="Comma-separated list of environments (e.g., dev,stage,prod)"
    ),
    config_type: str = typer.Option(
        "full",
        "--type",
        help="Configuration type: basic, kubernetes, docker, full"
    ),
    with_secrets: bool = typer.Option(
        False,
        "--with-secrets",
        help="Generate secrets templates"
    )
) -> None:
    """Generate multi-environment configurations with inheritance"""
    with handle_cli_errors():
        MultiEnvCommands.multi_env(project_path, environments, config_type, with_secrets)


@app.command()
def backup(
    action: str = typer.Argument(
        "create",
        help="Action: create, restore, or list"
    ),
    project_path: str = typer.Argument(
        ".",
        help="Path to the DevOps project"
    ),
    backup_file: Optional[str] = typer.Option(
        None,
        "--file",
        help="Backup file path for restore action"
    ),
    include_config: bool = typer.Option(
        True,
        "--include-config/--no-config",
        help="Include configuration files in backup"
    ),
    compress: bool = typer.Option(
        True,
        "--compress/--no-compress",
        help="Compress backup file"
    ),
) -> None:
    """Create and restore project backups"""
    with handle_cli_errors():
        BackupCommands.backup(action, project_path, backup_file, include_config, compress)


@app.command()
def profile(
    action: str = typer.Argument(..., help="Action: save, load, list, delete"),
    name: Optional[str] = typer.Option(None, "--name", help="Profile name"),
    file: Optional[str] = typer.Option(None, "--file", help="Profile file path"),
) -> None:
    """Manage project configuration profiles"""
    with handle_cli_errors():
        ProfileCommands.profile(action, name, file)


@app.command()
def version() -> None:
    """Show version information"""
    try:
        from . import __version__
    except ImportError:
        __version__ = "1.6.0"
    console.print(f"[bold blue]DevOps Project Generator[/bold blue] v{__version__}")


@app.command()
def list_options() -> None:
    """List all available options"""
    from .utils import format_file_size
    
    console.print(Panel.fit(
        "[bold blue]📋 Available Options[/bold blue]",
        border_style="blue"
    ))
    
    # Pipeline Framework Options
    console.print("\n[bold]🔄 Pipeline Frameworks:[/bold]")
    pipeline_table = Table()
    pipeline_table.add_column("Option", style="cyan")
    pipeline_table.add_column("Description")
    pipeline_table.add_row("nodejs-typescript", "Node.js + TypeScript pipelines")
    pipeline_table.add_row("python", "Python application pipelines")
    pipeline_table.add_row("java-maven", "Enterprise Java pipelines")
    pipeline_table.add_row("go", "Go application pipelines")
    pipeline_table.add_row("docker-multistage", "Containerized application pipelines")
    pipeline_table.add_row("terraform-module", "Infrastructure module pipelines")
    pipeline_table.add_row("kubernetes-operator", "Kubernetes operator pipelines")
    pipeline_table.add_row("microservice", "Microservice architecture pipelines")
    console.print(pipeline_table)
    
    # CI/CD Options
    console.print("\n[bold]🔄 CI/CD Platforms:[/bold]")
    ci_table = Table()
    ci_table.add_column("Option", style="cyan")
    ci_table.add_column("Description")
    ci_table.add_row("github-actions", "GitHub Actions workflows")
    ci_table.add_row("gitlab-ci", "GitLab CI/CD pipelines")
    ci_table.add_row("jenkins", "Jenkins pipeline files")
    ci_table.add_row("azure-pipelines", "Azure DevOps pipelines")
    ci_table.add_row("gitlab-runners", "GitLab Runners")
    ci_table.add_row("none", "No CI/CD")
    console.print(ci_table)
    
    # Infrastructure Options
    console.print("\n[bold]☁️ Infrastructure Patterns:[/bold]")
    infra_table = Table()
    infra_table.add_column("Option", style="cyan")
    infra_table.add_column("Description")
    infra_table.add_row("aws-vpc-eks", "Amazon EKS with VPC networking")
    infra_table.add_row("azure-vnet-aks", "Azure AKS with virtual networking")
    infra_table.add_row("gcp-vpc-gke", "Google GKE with VPC networking")
    infra_table.add_row("multicloud-terraform", "Cross-cloud infrastructure")
    infra_table.add_row("kubernetes-onprem", "On-premises Kubernetes")
    infra_table.add_row("aws-ecs-fargate", "Serverless container orchestration")
    infra_table.add_row("ansible-automation", "Configuration management")
    console.print(infra_table)
    
    # Deployment Options
    console.print("\n[bold]🚀 Deployment Strategies:[/bold]")
    deploy_table = Table()
    deploy_table.add_column("Option", style="cyan")
    deploy_table.add_column("Description")
    deploy_table.add_row("blue-green", "Zero-downtime deployments")
    deploy_table.add_row("canary", "Gradual rollout deployments")
    deploy_table.add_row("rolling", "Incremental updates")
    deploy_table.add_row("gitops-argocd", "Git-based continuous deployment")
    deploy_table.add_row("helm-charts", "Kubernetes package management")
    deploy_table.add_row("kustomize", "Kubernetes configuration management")
    deploy_table.add_row("serverless-lambda", "AWS Lambda deployments")
    console.print(deploy_table)
    
    # Environment Options
    console.print("\n[bold]🌍 Environment Options:[/bold]")
    env_table = Table()
    env_table.add_column("Option", style="cyan")
    env_table.add_column("Description")
    env_table.add_row("single", "Single environment")
    env_table.add_row("dev", "Development environment")
    env_table.add_row("dev,stage,prod", "Multi-environment setup")
    console.print(env_table)
    
    # Observability Options
    console.print("\n[bold]📊 Observability Stacks:[/bold]")
    obs_table = Table()
    obs_table.add_column("Option", style="cyan")
    obs_table.add_column("Description")
    obs_table.add_row("prometheus-grafana", "Metrics and visualization")
    obs_table.add_row("elk-stack", "Elasticsearch, Logstash, Kibana")
    obs_table.add_row("datadog", "Full-stack monitoring")
    obs_table.add_row("jaeger-prometheus", "Distributed tracing and metrics")
    obs_table.add_row("cloudwatch", "AWS native monitoring")
    obs_table.add_row("new-relic", "Application performance monitoring")
    console.print(obs_table)
    
    # Security Options
    console.print("\n[bold]🔒 Security Frameworks:[/bold]")
    sec_table = Table()
    sec_table.add_column("Option", style="cyan")
    sec_table.add_column("Description")
    sec_table.add_row("nist-csf", "NIST Cybersecurity Framework")
    sec_table.add_row("cis-benchmarks", "Center for Internet Security controls")
    sec_table.add_row("zero-trust", "Zero Trust Architecture")
    sec_table.add_row("soc2", "Service Organization Control 2")
    sec_table.add_row("gdpr", "General Data Protection Regulation")
    sec_table.add_row("hipaa", "Health Insurance Portability and Accountability Act")
    console.print(sec_table)


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


def _create_custom_template(template_name: str) -> None:
    """Create a new custom template"""
    console.print(f"[blue]📝 Creating custom template: {template_name}[/blue]")
    
    template_dir = Path.home() / ".devops-generator" / "templates" / template_name
    template_dir.mkdir(parents=True, exist_ok=True)
    
    # Create template structure
    subdirs = ["ci", "infra", "deploy", "monitoring", "security", "app"]
    for subdir in subdirs:
        (template_dir / subdir).mkdir(exist_ok=True)
    
    # Create template metadata
    metadata = {
        "name": template_name,
        "version": "1.0.0",
        "description": f"Custom template: {template_name}",
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


def _customize_template(template_name: str) -> None:
    """Customize an existing template"""
    template_dir = Path.home() / ".devops-generator" / "templates" / template_name
    
    if not template_dir.exists():
        console.print(f"[red]❌ Template '{template_name}' not found[/red]")
        console.print(f"[yellow]Available templates in: {template_dir.parent}[/yellow]")
        raise typer.Exit(1)
    
    console.print(f"[blue]🔧 Customizing template: {template_name}[/blue]")
    
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
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[blue]📤 Exporting templates to: {output_path}[/blue]")
    
    # Get the built-in templates directory
    builtin_templates = Path(__file__).parent.parent / "templates"
    
    if builtin_templates.exists():
        import shutil
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


@app.command()
def backup(
    action: str = typer.Argument(
        "create",
        help="Action: create, restore, or list"
    ),
    project_path: str = typer.Argument(
        ".",
        help="Path to the DevOps project"
    ),
    backup_file: Optional[str] = typer.Option(
        None,
        "--file",
        help="Backup file path for restore action"
    ),
    include_config: bool = typer.Option(
        True,
        "--include-config/--no-config",
        help="Include configuration files in backup"
    ),
    compress: bool = typer.Option(
        True,
        "--compress/--no-compress",
        help="Compress backup file"
    ),
) -> None:
    """Create and restore project backups"""
    project_path = Path(project_path).resolve()
    
    if action == "create":
        _create_backup(project_path, include_config, compress)
    elif action == "restore":
        if not backup_file:
            console.print("[red]❌ Backup file required for restore action[/red]")
            console.print("[yellow]Usage: devops-project-generator backup restore --file <backup-file>[/yellow]")
            raise typer.Exit(1)
        _restore_backup(project_path, backup_file)
    elif action == "list":
        _list_backups()
    else:
        console.print(f"[red]❌ Unknown action: {action}[/red]")
        console.print("[yellow]Available actions: create, restore, list[/yellow]")
        raise typer.Exit(1)


def _create_backup(project_path: Path, include_config: bool, compress: bool) -> None:
    """Create a backup of the project"""
    if not project_path.exists():
        console.print(f"[red]❌ Project path '{project_path}' does not exist[/red]")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        "[bold blue]💾 Creating Project Backup[/bold blue]\n"
        "[dim]Archive project files and configuration[/dim]",
        border_style="blue"
    ))
    
    # Generate backup filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{project_path.name}_backup_{timestamp}"
    
    if compress:
        backup_file = project_path.parent / f"{backup_name}.tar.gz"
    else:
        backup_file = project_path.parent / f"{backup_name}.tar"
    
    console.print(f"[blue]📦 Creating backup: {backup_file.name}[/blue]")
    
    try:
        import tarfile
        
        with tarfile.open(backup_file, "w:gz" if compress else "w") as tar:
            # Add project files
            for item in project_path.rglob("*"):
                if item.is_file():
                    # Skip certain files if not including config
                    if not include_config and any(pattern in item.name for pattern in [".env", "secret", "key"]):
                        continue
                    
                    arcname = str(item.relative_to(project_path.parent))
                    tar.add(item, arcname=arcname)
        
        # Create backup metadata
        backup_info = {
            "project_name": project_path.name,
            "created": datetime.datetime.now().isoformat(),
            "size_bytes": backup_file.stat().st_size,
            "include_config": include_config,
            "compressed": compress,
            "file_count": len(list(project_path.rglob("*"))),
            "version": "1.2.0"
        }
        
        metadata_file = backup_file.with_suffix(".json")
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(backup_info, f, indent=2)
        
        size_mb = backup_file.stat().st_size / (1024 * 1024)
        console.print(f"[green]✅ Backup created successfully![/green]")
        console.print(f"  File: {backup_file.name}")
        console.print(f"  Size: {size_mb:.2f} MB")
        console.print(f"  Files: {backup_info['file_count']}")
        
    except Exception as e:
        console.print(f"[red]❌ Backup failed: {str(e)}[/red]")
        raise typer.Exit(1)


def _restore_backup(project_path: Path, backup_file: str) -> None:
    """Restore a project from backup"""
    backup_path = Path(backup_file)
    
    if not backup_path.exists():
        console.print(f"[red]❌ Backup file '{backup_file}' does not exist[/red]")
        raise typer.Exit(1)
    
    # Check for metadata file
    metadata_file = backup_path.with_suffix(".json")
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            backup_info = json.load(f)
        
        console.print(Panel.fit(
            f"[bold blue]🔄 Restoring Project Backup[/bold blue]\n"
            f"[dim]Project: {backup_info.get('project_name', 'Unknown')}[/dim]\n"
            f"[dim]Created: {backup_info.get('created', 'Unknown')}[/dim]",
            border_style="blue"
        ))
    else:
        console.print(Panel.fit(
            "[bold blue]🔄 Restoring Project Backup[/bold blue]\n"
            "[dim]Backup information not available[/dim]",
            border_style="blue"
        ))
    
    # Check if project directory already exists
    if project_path.exists():
        console.print(f"[yellow]⚠️  Project directory '{project_path.name}' already exists[/yellow]")
        if not typer.confirm("Continue and overwrite?"):
            console.print("[dim]Operation cancelled.[/dim]")
            raise typer.Exit(0)
        
        # Remove existing directory
        shutil.rmtree(project_path)
    
    console.print(f"[blue]📦 Restoring from: {backup_path.name}[/blue]")
    
    try:
        import tarfile
        
        with tarfile.open(backup_path, "r:*") as tar:
            tar.extractall(project_path.parent)
        
        console.print(f"[green]✅ Project restored successfully![/green]")
        console.print(f"  Location: {project_path}")
        console.print(f"[yellow]💡 Run 'devops-project-generator validate {project_path.name}' to check the project[/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ Restore failed: {str(e)}[/red]")
        raise typer.Exit(1)


def _list_backups() -> None:
    """List all available backups"""
    console.print(Panel.fit(
        "[bold blue]📋 Available Backups[/bold blue]\n"
        "[dim]Project backups in current directory[/dim]",
        border_style="blue"
    ))
    
    current_dir = Path.cwd()
    backup_files = []
    
    # Find backup files
    for item in current_dir.glob("*backup*.tar*"):
        if item.is_file():
            backup_files.append(item)
    
    if not backup_files:
        console.print("[yellow]No backup files found in current directory[/yellow]")
        return
    
    console.print()
    table = Table()
    table.add_column("Backup File", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Created", style="blue")
    table.add_column("Project", style="yellow")
    
    for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
        size_mb = backup_file.stat().st_size / (1024 * 1024)
        mtime = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
        
        # Try to get project name from filename
        project_name = backup_file.name.split("_backup_")[0] if "_backup_" in backup_file.name else "Unknown"
        
        # Check for metadata
        metadata_file = backup_file.with_suffix(".json")
        created = mtime.strftime("%Y-%m-%d %H:%M")
        
        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                project_name = metadata.get("project_name", project_name)
                created = metadata.get("created", created)
                if isinstance(created, str):
                    created = created[:16]  # Just date and time
            except:
                pass
        
        table.add_row(
            backup_file.name,
            f"{size_mb:.1f} MB",
            created,
            project_name
        )
    
    console.print(table)


@app.command()
def health(
    project_path: str = typer.Argument(
        ".",
        help="Path to the DevOps project to check"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        help="Show detailed health analysis"
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Attempt to fix health issues automatically"
    ),
) -> None:
    """Perform comprehensive health check on DevOps project"""
    project_path = Path(project_path).resolve()
    
    if not project_path.exists():
        console.print(f"[red]❌ Project path '{project_path}' does not exist[/red]")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        "[bold blue]🏥 Project Health Check[/bold blue]\n"
        "[dim]Comprehensive analysis of project health and best practices[/dim]",
        border_style="blue"
    ))
    
    # Perform health check
    health_report = _perform_health_check(project_path, detailed)
    
    # Display results
    _display_health_report(health_report, detailed)
    
    # Auto-fix if requested
    if fix and health_report["fixable_issues"]:
        console.print("\n[yellow]🔧 Attempting to fix health issues...[/yellow]")
        _fix_health_issues(project_path, health_report["fixable_issues"])
    
    # Overall health score
    _display_health_score(health_report)


def _perform_health_check(project_path: Path, detailed: bool) -> dict:
    """Perform comprehensive health check"""
    report = {
        "overall_score": 0,
        "categories": {
            "structure": {"score": 0, "issues": [], "fixable_issues": [], "checks_passed": []},
            "security": {"score": 0, "issues": [], "fixable_issues": [], "checks_passed": []},
            "performance": {"score": 0, "issues": [], "fixable_issues": [], "checks_passed": []},
            "maintenance": {"score": 0, "issues": [], "fixable_issues": [], "checks_passed": []},
            "documentation": {"score": 0, "issues": [], "fixable_issues": [], "checks_passed": []}
        },
        "recommendations": [],
        "critical_issues": [],
        "fixable_issues": []
    }
    
    # Structure health
    _check_structure_health(project_path, report["categories"]["structure"])
    
    # Security health
    _check_security_health(project_path, report["categories"]["security"])
    
    # Performance health
    _check_performance_health(project_path, report["categories"]["performance"])
    
    # Maintenance health
    _check_maintenance_health(project_path, report["categories"]["maintenance"])
    
    # Documentation health
    _check_documentation_health(project_path, report["categories"]["documentation"])
    
    # Calculate overall score
    total_score = sum(cat["score"] for cat in report["categories"].values())
    report["overall_score"] = total_score // len(report["categories"])
    
    # Collect all issues
    for category in report["categories"].values():
        report["critical_issues"].extend([issue for issue in category["issues"] if "critical" in issue.lower()])
        report["fixable_issues"].extend(category["fixable_issues"])
    
    # Generate recommendations
    report["recommendations"] = _generate_health_recommendations(report)
    
    return report


def _check_structure_health(project_path: Path, structure: dict) -> None:
    """Check project structure health"""
    checks = {
        "required_dirs": ["app", "ci", "infra", "deploy", "monitoring", "security"],
        "required_files": ["README.md", "Makefile", ".gitignore"],
        "recommended_dirs": ["scripts", "docs", "tests"],
        "recommended_files": ["Dockerfile", "docker-compose.yml"]
    }
    
    score = 100
    
    # Check required directories
    for dir_name in checks["required_dirs"]:
        dir_path = project_path / dir_name
        if dir_path.exists():
            structure["checks_passed"].append(f"✅ {dir_name}/ directory exists")
        else:
            structure["issues"].append(f"❌ Missing required {dir_name}/ directory")
            structure["fixable_issues"].append(("create_dir", dir_name))
            score -= 15
    
    # Check required files
    for file_name in checks["required_files"]:
        file_path = project_path / file_name
        if file_path.exists():
            structure["checks_passed"].append(f"✅ {file_name} exists")
        else:
            structure["issues"].append(f"❌ Missing required {file_name}")
            if file_name == "README.md":
                structure["fixable_issues"].append(("create_readme", None))
            elif file_name == "Makefile":
                structure["fixable_issues"].append(("create_makefile", None))
            elif file_name == ".gitignore":
                structure["fixable_issues"].append(("create_gitignore", None))
            score -= 10
    
    # Check recommended items
    for dir_name in checks["recommended_dirs"]:
        dir_path = project_path / dir_name
        if dir_path.exists():
            structure["checks_passed"].append(f"✅ {dir_name}/ directory exists")
        else:
            structure["issues"].append(f"⚠️  Consider adding {dir_name}/ directory")
            score -= 5
    
    structure["score"] = max(0, score)


def _check_security_health(project_path: Path, security: dict) -> None:
    """Check security health"""
    score = 100
    
    # Check for secrets
    secret_patterns = [".env", "secret", "key", "password", "token"]
    for item in project_path.rglob("*"):
        if item.is_file() and any(pattern in item.name.lower() for pattern in secret_patterns):
            if item.suffix in [".txt", ".yml", ".yaml", ".json", ".env"]:
                security["issues"].append(f"🔒 Potential secret file: {item.relative_to(project_path)}")
                score -= 20
    
    # Check for security directories
    security_dir = project_path / "security"
    if security_dir.exists():
        security["checks_passed"].append("✅ Security directory exists")
        security_files = list(security_dir.rglob("*.yml")) + list(security_dir.rglob("*.yaml"))
        if security_files:
            security["checks_passed"].append(f"✅ Found {len(security_files)} security configuration files")
        else:
            security["issues"].append("⚠️  Security directory exists but no configuration files")
            score -= 10
    else:
        security["issues"].append("❌ No security configuration found")
        score -= 25
    
    # Check .gitignore for sensitive files
    gitignore_path = project_path / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            gitignore_content = f.read().lower()
        
        ignored_patterns = [".env", "secret", "key", "*.pem", "*.p12"]
        ignored_count = sum(1 for pattern in ignored_patterns if pattern in gitignore_content)
        
        if ignored_count >= 3:
            security["checks_passed"].append("✅ .gitignore properly excludes sensitive files")
        else:
            security["issues"].append("⚠️  .gitignore may not exclude all sensitive files")
            security["fixable_issues"].append(("update_gitignore", None))
            score -= 15
    else:
        security["issues"].append("❌ No .gitignore file found")
        score -= 20
    
    security["score"] = max(0, score)


def _check_performance_health(project_path: Path, performance: dict) -> None:
    """Check performance-related health"""
    score = 100
    
    # Check for Docker files
    docker_files = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]
    docker_found = any((project_path / f).exists() for f in docker_files)
    
    if docker_found:
        performance["checks_passed"].append("✅ Containerization files found")
    else:
        performance["issues"].append("⚠️  No containerization files found")
        performance["fixable_issues"].append(("create_dockerfile", None))
        score -= 15
    
    # Check for CI/CD optimization
    ci_dir = project_path / "ci"
    if ci_dir.exists():
        ci_files = list(ci_dir.rglob("*.yml")) + list(ci_dir.rglob("*.yaml"))
        if ci_files:
            performance["checks_passed"].append("✅ CI/CD configuration found")
            
            # Check for caching in CI files
            cache_found = False
            for ci_file in ci_files:
                try:
                    with open(ci_file, "r", encoding="utf-8") as f:
                        content = f.read().lower()
                        if "cache" in content:
                            cache_found = True
                            break
                except:
                    pass
            
            if cache_found:
                performance["checks_passed"].append("✅ CI/CD caching configured")
            else:
                performance["issues"].append("⚠️  Consider adding CI/CD caching for better performance")
                score -= 10
        else:
            performance["issues"].append("❌ CI/CD directory exists but no configuration files")
            score -= 20
    
    # Check project size
    total_size = sum(f.stat().st_size for f in project_path.rglob("*") if f.is_file())
    size_mb = total_size / (1024 * 1024)
    
    if size_mb > 100:
        performance["issues"].append(f"⚠️  Large project size: {size_mb:.1f} MB")
        performance["fixable_issues"].append(("optimize_size", None))
        score -= 10
    else:
        performance["checks_passed"].append(f"✅ Reasonable project size: {size_mb:.1f} MB")
    
    performance["score"] = max(0, score)


def _check_maintenance_health(project_path: Path, maintenance: dict) -> None:
    """Check maintenance-related health"""
    score = 100
    
    # Check for automation scripts
    scripts_dir = project_path / "scripts"
    if scripts_dir.exists():
        script_files = list(scripts_dir.rglob("*.sh")) + list(scripts_dir.rglob("*.py"))
        if script_files:
            maintenance["checks_passed"].append(f"✅ Found {len(script_files)} automation scripts")
        else:
            maintenance["issues"].append("⚠️  Scripts directory exists but no scripts found")
            score -= 10
    else:
        maintenance["issues"].append("⚠️  No automation scripts directory")
        maintenance["fixable_issues"].append(("create_scripts_dir", None))
        score -= 15
    
    # Check for Makefile targets
    makefile_path = project_path / "Makefile"
    if makefile_path.exists():
        try:
            with open(makefile_path, "r", encoding="utf-8") as f:
                makefile_content = f.read()
            
            common_targets = ["build", "deploy", "test", "clean"]
            found_targets = [target for target in common_targets if f"{target}:" in makefile_content]
            
            if len(found_targets) >= 3:
                maintenance["checks_passed"].append(f"✅ Makefile has {len(found_targets)} common targets")
            else:
                maintenance["issues"].append(f"⚠️  Makefile has only {len(found_targets)} common targets")
                score -= 10
        except:
            maintenance["issues"].append("❌ Error reading Makefile")
            score -= 5
    
    # Check for recent activity
    import time
    current_time = time.time()
    recent_files = []
    
    for item in project_path.rglob("*"):
        if item.is_file():
            file_age = current_time - item.stat().st_mtime
            if file_age < 7 * 24 * 60 * 60:  # Less than 7 days
                recent_files.append(item)
    
    if len(recent_files) >= 3:
        maintenance["checks_passed"].append(f"✅ Recent activity: {len(recent_files)} files modified in last 7 days")
    else:
        maintenance["issues"].append("⚠️  Low recent activity - project may need maintenance")
        score -= 10
    
    maintenance["score"] = max(0, score)


def _check_documentation_health(project_path: Path, documentation: dict) -> None:
    """Check documentation health"""
    score = 100
    
    # Check README quality
    readme_path = project_path / "README.md"
    if readme_path.exists():
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_content = f.read()
            
            readme_size = len(readme_content)
            sections = ["#", "##", "###"]
            section_count = sum(readme_content.count(section) for section in sections)
            
            if readme_size > 1000 and section_count >= 5:
                documentation["checks_passed"].append("✅ Comprehensive README documentation")
            elif readme_size > 500:
                documentation["issues"].append("⚠️  README could be more detailed")
                score -= 10
            else:
                documentation["issues"].append("❌ README is too short")
                documentation["fixable_issues"].append(("enhance_readme", None))
                score -= 20
        except:
            documentation["issues"].append("❌ Error reading README")
            score -= 15
    else:
        documentation["issues"].append("❌ No README.md file found")
        score -= 30
    
    # Check for additional documentation
    docs_dir = project_path / "docs"
    if docs_dir.exists():
        doc_files = list(docs_dir.rglob("*.md")) + list(docs_dir.rglob("*.txt"))
        if doc_files:
            documentation["checks_passed"].append(f"✅ Found {len(doc_files)} additional documentation files")
        else:
            documentation["issues"].append("⚠️  docs directory exists but no documentation files")
            score -= 5
    else:
        documentation["issues"].append("⚠️  No docs directory found")
        score -= 10
    
    # Check for inline documentation
    code_files = []
    for ext in [".py", ".js", ".ts", ".go", ".java"]:
        code_files.extend(project_path.rglob(f"*{ext}"))
    
    documented_files = 0
    for code_file in code_files[:20]:  # Check first 20 files
        try:
            with open(code_file, "r", encoding="utf-8") as f:
                content = f.read()
                if any(marker in content for marker in ["#", "//", "/*", "*"]):
                    documented_files += 1
        except:
            pass
    
    if code_files and documented_files / len(code_files) > 0.7:
        documentation["checks_passed"].append("✅ Good inline documentation coverage")
    elif code_files:
        documentation["issues"].append("⚠️  Consider adding more inline documentation")
        score -= 10
    
    documentation["score"] = max(0, score)


def _generate_health_recommendations(report: dict) -> list:
    """Generate health improvement recommendations"""
    recommendations = []
    
    if report["overall_score"] < 60:
        recommendations.append("🚨 Project needs significant improvement - focus on critical issues first")
    elif report["overall_score"] < 80:
        recommendations.append("⚡ Good foundation - address the identified issues to reach excellence")
    else:
        recommendations.append("🎉 Excellent project health! Consider sharing your practices")
    
    # Category-specific recommendations
    for category_name, category_data in report["categories"].items():
        if category_data["score"] < 70:
            if category_name == "structure":
                recommendations.append("🏗️  Improve project structure with missing directories and files")
            elif category_name == "security":
                recommendations.append("🔒 Enhance security with proper secrets management and policies")
            elif category_name == "performance":
                recommendations.append("⚡ Optimize performance with caching and containerization")
            elif category_name == "maintenance":
                recommendations.append("🔧 Add automation scripts and improve maintainability")
            elif category_name == "documentation":
                recommendations.append("📚 Enhance documentation for better project understanding")
    
    return recommendations


def _display_health_report(report: dict, detailed: bool) -> None:
    """Display comprehensive health report"""
    console.print(f"\n[bold]🏥 Overall Health Score: {report['overall_score']}/100[/bold]")
    
    # Health score color coding
    if report["overall_score"] >= 80:
        console.print("[green]✅ Excellent project health[/green]")
    elif report["overall_score"] >= 60:
        console.print("[yellow]⚠️  Good project health with room for improvement[/yellow]")
    else:
        console.print("[red]❌ Project needs attention[/red]")
    
    # Category breakdown
    console.print(f"\n[bold]📊 Category Breakdown:[/bold]")
    for category_name, category_data in report["categories"].items():
        score = category_data["score"]
        icon = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        console.print(f"  {icon} {category_name.title()}: {score}/100")
    
    # Critical issues
    if report["critical_issues"]:
        console.print(f"\n[bold red]🚨 Critical Issues:[/bold red]")
        for issue in report["critical_issues"]:
            console.print(f"  {issue}")
    
    # Category details if detailed
    if detailed:
        for category_name, category_data in report["categories"].items():
            console.print(f"\n[bold]{category_name.title()} Details:[/bold]")
            
            if category_data["checks_passed"]:
                console.print("[green]✅ Passed Checks:[/green]")
                for check in category_data["checks_passed"][:5]:
                    console.print(f"  {check}")
                if len(category_data["checks_passed"]) > 5:
                    console.print(f"  ... and {len(category_data['checks_passed']) - 5} more")
            
            if category_data["issues"]:
                console.print("[red]❌ Issues:[/red]")
                for issue in category_data["issues"]:
                    console.print(f"  {issue}")


def _fix_health_issues(project_path: Path, fixable_issues: list) -> None:
    """Attempt to fix health issues automatically"""
    for issue_type, issue_data in fixable_issues:
        try:
            if issue_type == "create_dir":
                (project_path / issue_data).mkdir(parents=True, exist_ok=True)
                console.print(f"[green]✅ Created directory: {issue_data}/[/green]")
            
            elif issue_type == "create_readme":
                readme_content = """# Project Name

## Description
Add your project description here.

## Installation
```bash
# Add installation instructions
```

## Usage
```bash
# Add usage instructions
```

## Contributing
Add contributing guidelines here.

## License
Add license information here.
"""
                with open(project_path / "README.md", "w", encoding="utf-8") as f:
                    f.write(readme_content)
                console.print("[green]✅ Created README.md[/green]")
            
            elif issue_type == "create_gitignore":
                gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env
.env.local
.env.*.local

# Secrets
*.key
*.pem
*.p12
secrets/
*.secret

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
                with open(project_path / ".gitignore", "w", encoding="utf-8") as f:
                    f.write(gitignore_content)
                console.print("[green]✅ Created .gitignore[/green]")
            
            elif issue_type == "create_scripts_dir":
                scripts_dir = project_path / "scripts"
                scripts_dir.mkdir(exist_ok=True)
                
                # Create sample script
                sample_script = """#!/bin/bash
# Sample automation script

echo "Running automation..."

# Add your automation commands here
"""
                with open(scripts_dir / "setup.sh", "w", encoding="utf-8") as f:
                    f.write(sample_script)
                os.chmod(scripts_dir / "setup.sh", 0o755)
                console.print("[green]✅ Created scripts directory with sample script[/green]")
        
        except Exception as e:
            console.print(f"[red]❌ Could not fix {issue_type}: {str(e)}[/red]")


def _display_health_score(report: dict) -> None:
    """Display final health score and recommendations"""
    console.print(f"\n[bold]🎯 Final Health Score: {report['overall_score']}/100[/bold]")
    
    if report["recommendations"]:
        console.print(f"\n[bold]💡 Recommendations:[/bold]")
        for rec in report["recommendations"]:
            console.print(f"  {rec}")




@app.command()
def profile(
    action: str = typer.Argument(..., help="Action: save, load, list, delete"),
    name: Optional[str] = typer.Option(None, "--name", help="Profile name"),
    file: Optional[str] = typer.Option(None, "--file", help="Profile file path"),
) -> None:
    """Manage project configuration profiles"""
    try:
        if action == "list":
            _list_profiles()
        elif action == "save":
            if not name:
                console.print("[red]❌ --name required for save action[/red]")
                raise typer.Exit(1)
            _save_profile(name)
        elif action == "load":
            if not name:
                console.print("[red]❌ --name required for load action[/red]")
                raise typer.Exit(1)
            _load_profile(name)
        elif action == "delete":
            if not name:
                console.print("[red]❌ --name required for delete action[/red]")
                raise typer.Exit(1)
            _delete_profile(name)
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("[yellow]Available actions: list, save, load, delete[/yellow]")
            raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Profile management error: {str(e)}")
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


def _get_profiles_dir() -> Path:
    """Get profiles directory"""
    home = Path.home()
    profiles_dir = home / ".devops-project-generator" / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    return profiles_dir


def _list_profiles() -> None:
    """List saved profiles"""
    profiles_dir = _get_profiles_dir()
    profiles = list(profiles_dir.glob("*.json"))
    
    console.print(Panel.fit(
        "[bold blue]📋 Saved Configuration Profiles[/bold blue]",
        border_style="blue"
    ))
    
    if not profiles:
        console.print("[yellow]No saved profiles found.[/yellow]")
        console.print("[dim]Use 'devops-project-generator profile save --name <name>' to create a profile[/dim]")
        return
    
    for profile_file in sorted(profiles):
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            console.print(f"\n[bold cyan]{profile_file.stem}[/bold cyan]")
            console.print(f"  📅 Created: {profile_data.get('created_at', 'Unknown')}")
            console.print(f"  🏷️  Description: {profile_data.get('description', 'No description')}")
            
            config = profile_data.get('config', {})
            if config.get('ci'):
                console.print(f"  🔧 CI/CD: {config['ci']}")
            if config.get('infra'):
                console.print(f"  🏗️  Infrastructure: {config['infra']}")
            if config.get('deploy'):
                console.print(f"  🚀 Deployment: {config['deploy']}")
            if config.get('observability'):
                console.print(f"  📊 Observability: {config['observability']}")
            if config.get('security'):
                console.print(f"  🔒 Security: {config['security']}")
                
        except Exception as e:
            console.print(f"[red]❌ Error reading profile {profile_file.name}: {str(e)}[/red]")


def _save_profile(name: str) -> None:
    """Save current configuration as a profile"""
    profiles_dir = _get_profiles_dir()
    profile_file = profiles_dir / f"{name}.json"
    
    if profile_file.exists():
        if not typer.confirm(f"Profile '{name}' already exists. Overwrite?"):
            console.print("[dim]Operation cancelled.[/dim]")
            return
    
    # Get current configuration from interactive mode or defaults
    console.print("[bold]🔧 Creating configuration profile[/bold]")
    
    config = {
        "ci": typer.prompt("CI/CD platform", default="github-actions"),
        "infra": typer.prompt("Infrastructure tool", default="terraform"),
        "deploy": typer.prompt("Deployment method", default="docker"),
        "envs": typer.prompt("Environments", default="single"),
        "observability": typer.prompt("Observability level", default="logs"),
        "security": typer.prompt("Security level", default="basic"),
    }
    
    profile_data = {
        "name": name,
        "description": typer.prompt("Description (optional)", default=""),
        "created_at": datetime.datetime.now().isoformat(),
        "config": config,
        "version": "1.6.0"
    }
    
    with open(profile_file, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, indent=2, ensure_ascii=False)
    
    console.print(f"[green]✅ Profile saved: {name}[/green]")
    console.print(f"[dim]Location: {profile_file}[/dim]")


def _load_profile(name: str) -> None:
    """Load and display a profile"""
    profiles_dir = _get_profiles_dir()
    profile_file = profiles_dir / f"{name}.json"
    
    if not profile_file.exists():
        console.print(f"[red]❌ Profile not found: {name}[/red]")
        raise typer.Exit(1)
    
    try:
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        console.print(Panel.fit(
            f"[bold blue]📋 Profile: {name}[/bold blue]",
            border_style="blue"
        ))
        
        console.print(f"📅 Created: {profile_data.get('created_at', 'Unknown')}")
        console.print(f"🏷️  Description: {profile_data.get('description', 'No description')}")
        
        config = profile_data.get('config', {})
        console.print(f"\n[bold]Configuration:[/bold]")
        console.print(f"  🔧 CI/CD: {config.get('ci', 'none')}")
        console.print(f"  🏗️  Infrastructure: {config.get('infra', 'none')}")
        console.print(f"  🚀 Deployment: {config.get('deploy', 'vm')}")
        console.print(f"  🌍 Environments: {config.get('envs', 'single')}")
        console.print(f"  📊 Observability: {config.get('observability', 'logs')}")
        console.print(f"  🔒 Security: {config.get('security', 'basic')}")
        
        # Show command to use this profile
        cmd_parts = []
        for key, value in config.items():
            if value and value != "none":
                cmd_parts.append(f"--{key} {value}")
        
        console.print(f"\n[bold]Usage command:[/bold]")
        console.print(f"  devops-project-generator init {' '.join(cmd_parts)} --name <project-name>")
        
    except Exception as e:
        console.print(f"[red]❌ Error loading profile: {str(e)}[/red]")
        raise typer.Exit(1)


def _delete_profile(name: str) -> None:
    """Delete a saved profile"""
    profiles_dir = _get_profiles_dir()
    profile_file = profiles_dir / f"{name}.json"
    
    if not profile_file.exists():
        console.print(f"[red]❌ Profile not found: {name}[/red]")
        raise typer.Exit(1)
    
    if typer.confirm(f"Delete profile '{name}'?"):
        profile_file.unlink()
        console.print(f"[green]✅ Profile deleted: {name}[/green]")
    else:
        console.print("[dim]Operation cancelled.[/dim]")


@app.command()
def test(
    project_path: str = typer.Argument(..., help="Path to project to test"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
) -> None:
    """Run integration tests on generated project"""
    try:
        project_dir = Path(project_path)
        
        if not project_dir.exists():
            console.print(f"[red]❌ Project not found: {project_path}[/red]")
            raise typer.Exit(1)
        
        console.print(Panel.fit(
            "[bold blue]🧪 Running Integration Tests[/bold blue]",
            border_style="blue"
        ))
        
        test_results = _run_integration_tests(project_dir, verbose)
        
        # Display results
        console.print(f"\n[bold]📊 Test Results:[/bold]")
        console.print(f"  ✅ Passed: {test_results['passed']}")
        console.print(f"  ❌ Failed: {test_results['failed']}")
        console.print(f"  ⚠️  Warnings: {test_results['warnings']}")
        console.print(f"  📈 Score: {test_results['score']}/100")
        
        if test_results['failed'] > 0:
            console.print("\n[bold red]❌ Failed Tests:[/bold red]")
            for test in test_results['failed_tests']:
                console.print(f"  • {test}")
            raise typer.Exit(1)
        else:
            console.print("\n[green]✅ All tests passed![/green]")
            
    except Exception as e:
        logger.error(f"Test execution error: {str(e)}")
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


def _run_integration_tests(project_dir: Path, verbose: bool) -> Dict[str, Any]:
    """Run comprehensive integration tests"""
    results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0,
        'score': 0,
        'failed_tests': []
    }
    
    tests = [
        ("Project Structure", _test_project_structure),
        ("Configuration Files", _test_config_files),
        ("Security Files", _test_security_files),
        ("CI/CD Files", _test_cicd_files),
        ("Documentation", _test_documentation),
        ("Scripts", _test_scripts),
    ]
    
    for test_name, test_func in tests:
        try:
            if verbose:
                console.print(f"  🔍 Running {test_name}...")
            
            test_result = test_func(project_dir)
            
            if test_result['passed']:
                results['passed'] += 1
                if verbose:
                    console.print(f"    ✅ {test_name} passed")
            else:
                results['failed'] += 1
                results['failed_tests'].append(f"{test_name}: {test_result['message']}")
                if verbose:
                    console.print(f"    ❌ {test_name} failed: {test_result['message']}")
            
            if test_result.get('warning'):
                results['warnings'] += 1
                if verbose:
                    console.print(f"    ⚠️  {test_name}: {test_result['warning']}")
                    
        except Exception as e:
            results['failed'] += 1
            results['failed_tests'].append(f"{test_name}: {str(e)}")
            if verbose:
                console.print(f"    ❌ {test_name} error: {str(e)}")
    
    # Calculate score
    total_tests = len(tests)
    results['score'] = int((results['passed'] / total_tests) * 100)
    
    return results


def _test_project_structure(project_dir: Path) -> Dict[str, Any]:
    """Test basic project structure"""
    required_dirs = ['app', 'scripts', 'docs']
    missing_dirs = [d for d in required_dirs if not (project_dir / d).exists()]
    
    if missing_dirs:
        return {'passed': False, 'message': f"Missing directories: {', '.join(missing_dirs)}"}
    
    return {'passed': True}


def _test_config_files(project_dir: Path) -> Dict[str, Any]:
    """Test configuration files"""
    config_files = ['README.md', 'Makefile', '.gitignore']
    missing_files = [f for f in config_files if not (project_dir / f).exists()]
    
    if missing_files:
        return {'passed': False, 'message': f"Missing config files: {', '.join(missing_files)}"}
    
    # Check README content
    readme_file = project_dir / 'README.md'
    if readme_file.exists():
        content = readme_file.read_text(encoding='utf-8')
        if len(content) < 100:
            return {'passed': False, 'message': "README.md too short"}
    
    return {'passed': True}


def _test_security_files(project_dir: Path) -> Dict[str, Any]:
    """Test security configuration"""
    security_dir = project_dir / 'security'
    
    if security_dir.exists():
        security_files = list(security_dir.glob('*.yml')) + list(security_dir.glob('*.yaml'))
        if not security_files:
            return {'passed': False, 'message': "Security directory exists but no security files found"}
    
    return {'passed': True, 'warning': "No security files found (optional)"}


def _test_cicd_files(project_dir: Path) -> Dict[str, Any]:
    """Test CI/CD configuration"""
    ci_dir = project_dir / 'ci'
    
    if ci_dir.exists():
        ci_files = list(ci_dir.glob('*.yml')) + list(ci_dir.glob('*.yaml')) + list(ci_dir.glob('*jenkinsfile*'))
        if not ci_files:
            return {'passed': False, 'message': "CI directory exists but no CI files found"}
    
    return {'passed': True, 'warning': "No CI files found (optional)"}


def _test_documentation(project_dir: Path) -> Dict[str, Any]:
    """Test documentation"""
    docs_dir = project_dir / 'docs'
    readme_file = project_dir / 'README.md'
    
    if not docs_dir.exists():
        return {'passed': True, 'warning': "No docs directory found"}
    
    if not readme_file.exists():
        return {'passed': False, 'message': "No README.md found"}
    
    return {'passed': True}


def _test_scripts(project_dir: Path) -> Dict[str, Any]:
    """Test scripts"""
    scripts_dir = project_dir / 'scripts'
    
    if scripts_dir.exists():
        script_files = list(scripts_dir.glob('*.sh')) + list(scripts_dir.glob('*.py'))
        if not script_files:
            return {'passed': False, 'message': "Scripts directory exists but no scripts found"}
    
    return {'passed': True, 'warning': "No scripts found (optional)"}


@app.command()
def version() -> None:
    """Show version information"""
    try:
        from . import __version__
    except ImportError:
        __version__ = "1.6.0"
    console.print(f"[bold blue]DevOps Project Generator[/bold blue] v{__version__}")


@app.command()
def scan(
    project_path: str = typer.Argument(
        ".",
        help="Path to project to scan for dependencies"
    ),
    export: Optional[str] = typer.Option(
        None,
        "--export",
        help="Export report to file (e.g., report.json, report.yaml)"
    ),
    format: str = typer.Option(
        "json",
        "--format",
        help="Export format: json or yaml"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        help="Show detailed dependency information"
    )
) -> None:
    """Scan project dependencies and security vulnerabilities"""
    try:
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            console.print(f"[red]❌ Project path does not exist: {project_path}[/red]")
            raise typer.Exit(1)
        
        if not project_path.is_dir():
            console.print(f"[red]❌ Path is not a directory: {project_path}[/red]")
            raise typer.Exit(1)
        
        console.print(f"[bold]🔍 Scanning dependencies for:[/bold] {project_path}")
        
        # Perform scan
        scanner = DependencyScanner(str(project_path))
        result = scanner.scan_project()
        
        # Display results
        console.print("\n[bold]📊 Scan Results:[/bold]")
        
        # Summary table
        summary_table = Table(title="Dependency Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="green")
        
        summary_table.add_row("Total Dependencies", str(result.total_dependencies))
        summary_table.add_row("Outdated Packages", str(result.outdated_packages))
        summary_table.add_row("Security Issues", str(result.security_issues))
        
        console.print(summary_table)
        
        # Recommendations
        if result.recommendations:
            console.print("\n[bold]💡 Recommendations:[/bold]")
            for i, rec in enumerate(result.recommendations, 1):
                console.print(f"  {i}. {rec}")
        
        # Detailed breakdown
        if detailed:
            console.print("\n[bold]📋 Detailed Dependencies:[/bold]")
            
            # Group by type
            deps_by_type = {}
            for dep in result.dependencies:
                if dep.dependency_type not in deps_by_type:
                    deps_by_type[dep.dependency_type] = []
                deps_by_type[dep.dependency_type].append(dep)
            
            for dep_type, deps in deps_by_type.items():
                console.print(f"\n[cyan]{dep_type.upper()} Dependencies:[/cyan]")
                
                dep_table = Table()
                dep_table.add_column("Name", style="white")
                dep_table.add_column("Version", style="yellow")
                dep_table.add_column("Source", style="dim")
                dep_table.add_column("Status", style="red")
                
                for dep in deps[:10]:  # Limit to 10 per type for readability
                    status = ""
                    if dep.outdated:
                        status += "⚠️ Outdated"
                    if dep.security_issues:
                        status += " 🚨 Security" if status else "🚨 Security"
                    if not status:
                        status = "✅ OK"
                    
                    dep_table.add_row(
                        dep.name,
                        dep.version or "unpinned",
                        dep.source_file,
                        status
                    )
                
                console.print(dep_table)
                
                if len(deps) > 10:
                    console.print(f"[dim]... and {len(deps) - 10} more {dep_type} dependencies[/dim]")
        
        # Export report
        if export:
            scanner.export_report(export, format)
            console.print(f"\n[green]✅ Report exported to:[/green] {export}")
        
        # Final status
        if result.security_issues > 0:
            console.print(f"\n[red]🚨 Found {result.security_issues} security issues - immediate attention required[/red]")
        elif result.outdated_packages > 0:
            console.print(f"\n[yellow]⚠️  Found {result.outdated_packages} outdated packages - recommend updates[/yellow]")
        else:
            console.print("\n[green]✅ No critical issues found[/green]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Scan cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        logger.error(f"Scan error: {str(e)}", exc_info=True)
        console.print(f"\n[red]❌ Scan failed: {str(e)}[/red]")
        console.print("[yellow]💡 Check the log file for details: devops-generator.log[/yellow]")
        raise typer.Exit(1)


@app.command()
def multi_env(
    project_path: str = typer.Argument(
        ".",
        help="Path to project for multi-environment configuration"
    ),
    environments: str = typer.Option(
        "dev,stage,prod",
        "--envs",
        help="Comma-separated list of environments (e.g., dev,stage,prod)"
    ),
    config_type: str = typer.Option(
        "full",
        "--type",
        help="Configuration type: basic, kubernetes, docker, full"
    ),
    with_secrets: bool = typer.Option(
        False,
        "--with-secrets",
        help="Generate secrets templates"
    )
) -> None:
    """Generate multi-environment configurations with inheritance"""
    try:
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            console.print(f"[red]❌ Project path does not exist: {project_path}[/red]")
            raise typer.Exit(1)
        
        if not project_path.is_dir():
            console.print(f"[red]❌ Path is not a directory: {project_path}[/red]")
            raise typer.Exit(1)
        
        # Parse environments
        env_list = [env.strip() for env in environments.split(",") if env.strip()]
        if not env_list:
            console.print("[red]❌ At least one environment must be specified[/red]")
            raise typer.Exit(1)
        
        console.print(f"[bold]🔧 Setting up multi-environment configs for:[/bold] {project_path}")
        console.print(f"[cyan]Environments:[/cyan] {', '.join(env_list)}")
        console.print(f"[cyan]Config Type:[/cyan] {config_type}")
        
        # Initialize generator
        generator = MultiEnvConfigGenerator(str(project_path))
        
        # Setup environment structure
        generator.setup_environment_structure(env_list)
        
        # Add base configuration
        base_config = {
            'app': {
                'name': '{{ project_name }}',
                'version': '1.0.0',
                'debug': False
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'pool_size': 10
            },
            'logging': {
                'level': 'INFO',
                'format': 'json'
            }
        }
        
        generator.add_base_config(base_config)
        
        # Add environment-specific overrides
        env_configs = {
            'dev': {
                'app': {'debug': True},
                'database': {'host': 'localhost', 'name': 'dev_db'},
                'logging': {'level': 'DEBUG'}
            },
            'stage': {
                'app': {'debug': False},
                'database': {'host': 'stage-db.example.com', 'name': 'stage_db'},
                'logging': {'level': 'INFO'}
            },
            'prod': {
                'app': {'debug': False},
                'database': {'host': 'prod-db.example.com', 'name': 'prod_db'},
                'logging': {'level': 'WARN'}
            }
        }
        
        for env in env_list:
            if env in env_configs:
                generator.add_environment_override(env, env_configs[env])
        
        # Add secrets if requested
        if with_secrets:
            import secrets as secrets_module
            for env in env_list:
                env_secrets = {
                    'database_password': f'{env}_db_password_123',
                    'api_key': f'{env}_api_key_placeholder',
                    'jwt_secret': secrets_module.token_urlsafe(32)
                }
                generator.add_secrets(env, env_secrets)
        
        # Generate configurations based on type
        if config_type in ['kubernetes', 'full']:
            generator.generate_kubernetes_configs(env_list)
            generator.generate_config_maps(env_list)
            if with_secrets:
                generator.generate_secrets_templates(env_list)
        
        if config_type in ['docker', 'full']:
            generator.generate_docker_compose_configs(env_list)
        
        if config_type in ['basic', 'full']:
            generator.generate_env_files(env_list)
        
        # Generate deployment script
        generator.generate_deployment_script(env_list)
        
        # Validate configurations
        validation_results = generator.validate_configurations()
        has_errors = any(errors for errors in validation_results.values())
        
        # Display results
        console.print("\n[bold]✅ Multi-Environment Configuration Generated![/bold]")
        
        # Structure table
        structure_table = Table(title="Generated Structure")
        structure_table.add_column("Directory/File", style="cyan")
        structure_table.add_column("Purpose", style="white")
        
        structure_table.add_row("config/", "Environment configurations")
        structure_table.add_row("config/secrets/", "Secrets templates")
        structure_table.add_row("scripts/deploy.sh", "Deployment script")
        
        if config_type in ['kubernetes', 'full']:
            structure_table.add_row("k8s/base/", "Base Kubernetes manifests")
            structure_table.add_row("k8s/overlays/", "Environment-specific overlays")
        
        if config_type in ['docker', 'full']:
            structure_table.add_row("docker/", "Docker Compose configurations")
        
        console.print(structure_table)
        
        # Environment summary
        console.print(f"\n[bold]🌍 Environment Summary:[/bold]")
        for env in env_list:
            env_config = generator.environments[env]
            console.print(f"  [cyan]{env.title()}:[/cyan]")
            console.print(f"    Config: {len(env_config.get_merged_config())} keys")
            console.print(f"    Secrets: {len(env_config.secrets)} items")
        
        # Validation results
        if has_errors:
            console.print("\n[red]⚠️  Validation Issues Found:[/red]")
            for env, errors in validation_results.items():
                if errors:
                    console.print(f"  [yellow]{env}:[/yellow]")
                    for error in errors:
                        console.print(f"    • {error}")
        else:
            console.print("\n[green]✅ All configurations validated successfully[/green]")
        
        # Next steps
        console.print(f"\n[bold]🚀 Next Steps:[/bold]")
        console.print(f"1. Review generated configurations in [cyan]config/[/cyan] directory")
        if with_secrets:
            console.print(f"2. Update secret values in [cyan]config/secrets/[/cyan]")
        console.print(f"3. Use deployment script: [cyan]./scripts/deploy.sh <environment>[/cyan]")
        
        if config_type in ['kubernetes', 'full']:
            console.print(f"4. Deploy with kubectl: [cyan]kubectl apply -k k8s/overlays/<env>[/cyan]")
        
        if config_type in ['docker', 'full']:
            console.print(f"4. Deploy with Docker: [cyan]docker-compose -f docker/docker-compose.<env>.yml up -d[/cyan]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        logger.error(f"Multi-env configuration error: {str(e)}", exc_info=True)
        console.print(f"\n[red]❌ Configuration generation failed: {str(e)}[/red]")
        console.print("[yellow]💡 Check the log file for details: devops-generator.log[/yellow]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
