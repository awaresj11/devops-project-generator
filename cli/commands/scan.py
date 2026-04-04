#!/usr/bin/env python3
"""
Scanning commands for DevOps Project Generator
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
