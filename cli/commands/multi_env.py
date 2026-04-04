#!/usr/bin/env python3
"""
Multi-environment commands for DevOps Project Generator
"""

import logging
import secrets as secrets_module
from pathlib import Path
from typing import List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


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
