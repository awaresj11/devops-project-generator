#!/usr/bin/env python3
"""
CLI command modules for DevOps Project Generator
"""

import os
import shutil
import json
import yaml
import datetime
import logging
import tarfile
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .utils import (
    format_duration, format_file_size, calculate_project_stats,
    show_success_message, show_error_message, show_warning_message,
    show_progress_spinner, safe_execute, validate_project_name,
    validate_output_path, create_backup_filename, get_profiles_dir,
    categorize_file, calculate_devops_score, generate_recommendations,
    safe_print
)

logger = logging.getLogger(__name__)
console = Console()


class ProjectCommands:
    """Project management commands"""
    
    @staticmethod
    def validate(project_path: str, fix: bool = False) -> None:
        """Validate a DevOps project structure and configuration"""
        from .cli import _validate_project_structure, _display_validation_results, _fix_project_issues
        
        project_path = Path(project_path)
        
        if not project_path.exists():
            console.print(f"[red]❌ Project path '{project_path}' does not exist[/red]")
            raise typer.Exit(1)
        
        console.print(Panel.fit(
            "[bold blue]🔍 Project Validation[/bold blue]\n"
            "[dim]Checking DevOps project structure and configuration[/dim]",
            border_style="blue"
        ))
        
        validation_results = _validate_project_structure(project_path)
        
        # Display results
        _display_validation_results(validation_results)
        
        # Auto-fix if requested
        if fix and validation_results["issues"]:
            console.print("\n[yellow]🔧 Attempting to fix issues...[/yellow]")
            _fix_project_issues(project_path, validation_results["issues"])
        
        # Exit with appropriate code
        if validation_results["critical_issues"]:
            console.print(f"\n[red]❌ Validation failed with {len(validation_results['critical_issues'])} critical issues[/red]")
            raise typer.Exit(1)
        elif validation_results["issues"]:
            console.print(f"\n[yellow]⚠️  Validation passed with {len(validation_results['issues'])} warnings[/yellow]")
        else:
            console.print("\n[green]✅ Project validation passed successfully![/green]")
    
    @staticmethod
    def info(project_path: str, detailed: bool = False) -> None:
        """Show detailed information and statistics about a DevOps project"""
        from .cli import _analyze_project, _display_project_info
        
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            console.print(f"[red]❌ Project path '{project_path}' does not exist[/red]")
            raise typer.Exit(1)
        
        console.print(Panel.fit(
            "[bold blue]📊 Project Information[/bold blue]\n"
            "[dim]Detailed analysis of DevOps project structure and components[/dim]",
            border_style="blue"
        ))
        
        # Gather project information
        project_stats = _analyze_project(project_path, detailed)
        
        # Display results
        _display_project_info(project_stats, detailed)
    
    @staticmethod
    def health(project_path: str, detailed: bool = False, fix: bool = False) -> None:
        """Perform comprehensive health check on DevOps project"""
        from .cli import _perform_health_check, _display_health_report, _fix_health_issues, _display_health_score
        
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
    
    @staticmethod
    def cleanup(project_path: str, force: bool = False, keep_config: bool = False) -> None:
        """Clean up a DevOps project and remove generated resources"""
        from .cli import _get_project_info, _display_project_summary, _cleanup_project, _display_cleanup_results
        
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            console.print(f"[red]❌ Project path '{project_path}' does not exist[/red]")
            raise typer.Exit(1)
        
        console.print(Panel.fit(
            "[bold red]🧹 Project Cleanup[/bold red]\n"
            "[dim]Remove generated DevOps project and resources[/dim]",
            border_style="red"
        ))
        
        # Show project info before cleanup
        project_info = _get_project_info(project_path)
        _display_project_summary(project_info)
        
        # Confirmation prompt
        if not force:
            console.print(f"\n[red]⚠️  This will permanently delete the project at:[/red]")
            console.print(f"[bold]{project_path}[/bold]")
            
            if not typer.confirm("\n[yellow]Are you sure you want to continue?[/yellow]"):
                console.print("[dim]Operation cancelled.[/dim]")
                raise typer.Exit(0)
        
        # Perform cleanup
        cleanup_results = _cleanup_project(project_path, keep_config)
        
        # Display results
        _display_cleanup_results(cleanup_results)


class ConfigCommands:
    """Configuration management commands"""
    
    @staticmethod
    def config(action: str, config_file: str = "devops-config.yaml") -> None:
        """Manage project configuration files"""
        from .cli import _create_config_file, _show_config_file, _validate_config_file
        
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


class TemplateCommands:
    """Template management commands"""
    
    @staticmethod
    def template(action: str, category: Optional[str] = None, name: Optional[str] = None, 
                output_dir: Optional[str] = None) -> None:
        """Manage and customize project templates"""
        from .cli import _list_available_templates, _create_custom_template, _customize_template, _export_templates
        
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


class BackupCommands:
    """Backup and restore commands"""
    
    @staticmethod
    def backup(action: str, project_path: str = ".", backup_file: Optional[str] = None,
               include_config: bool = True, compress: bool = True) -> None:
        """Create and restore project backups"""
        from .cli import _create_backup, _restore_backup, _list_backups
        
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


class ProfileCommands:
    """Profile management commands"""
    
    @staticmethod
    def profile(action: str, name: Optional[str] = None, file: Optional[str] = None) -> None:
        """Manage project configuration profiles"""
        from .cli import _list_profiles, _save_profile, _load_profile, _delete_profile
        
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


class TestCommands:
    """Testing commands"""
    
    @staticmethod
    def test(project_path: str, verbose: bool = False) -> None:
        """Run integration tests on generated project"""
        from .cli import _run_integration_tests
        
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


class ScanCommands:
    """Scanning commands"""
    
    @staticmethod
    def scan(project_path: str = ".", export: Optional[str] = None, 
             format: str = "json", detailed: bool = False) -> None:
        """Scan project dependencies and security vulnerabilities"""
        from generator.scanner import DependencyScanner
        
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


class MultiEnvCommands:
    """Multi-environment commands"""
    
    @staticmethod
    def multi_env(project_path: str = ".", environments: str = "dev,stage,prod",
                  config_type: str = "full", with_secrets: bool = False) -> None:
        """Generate multi-environment configurations with inheritance"""
        from generator.config_generator import MultiEnvConfigGenerator
        
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
