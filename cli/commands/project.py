#!/usr/bin/env python3
"""
Project management commands for DevOps Project Generator
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any

import typer
from rich.console import Console
from rich.panel import Panel

from ..utils import (
    show_success_message, show_error_message, show_warning_message,
    calculate_project_stats, format_file_size
)

logger = logging.getLogger(__name__)
console = Console()


def validate(project_path: str, fix: bool = False) -> None:
    """Validate a DevOps project structure and configuration"""
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


def info(project_path: str, detailed: bool = False) -> None:
    """Show detailed information and statistics about a DevOps project"""
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


def health(project_path: str, detailed: bool = False, fix: bool = False) -> None:
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


def cleanup(project_path: str, force: bool = False, keep_config: bool = False) -> None:
    """Clean up a DevOps project and remove generated resources"""
    import shutil
    
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


# =============================================================================
# INTERNAL HELPER FUNCTIONS
# =============================================================================

def _validate_project_structure(project_path: Path) -> dict:
    """Validate the project structure and return results"""
    results = {
        "critical_issues": [],
        "issues": [],
        "warnings": [],
        "passed_checks": []
    }
    
    # Check required directories
    required_dirs = [
        "app", "ci", "infra", "containers", "k8s", 
        "monitoring", "security", "scripts"
    ]
    
    for dir_name in required_dirs:
        dir_path = project_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            results["passed_checks"].append(f"✅ {dir_name}/ directory exists")
        else:
            results["issues"].append(f"❌ Missing {dir_name}/ directory")
    
    # Check required files
    required_files = [
        "README.md", "Makefile", ".gitignore"
    ]
    
    for file_name in required_files:
        file_path = project_path / file_name
        if file_path.exists() and file_path.is_file():
            results["passed_checks"].append(f"✅ {file_name} exists")
        else:
            results["critical_issues"].append(f"❌ Missing {file_name}")
    
    # Check script permissions
    script_files = [
        "scripts/setup.sh", "scripts/deploy.sh"
    ]
    
    for script in script_files:
        script_path = project_path / script
        if script_path.exists():
            if os.access(script_path, os.X_OK):
                results["passed_checks"].append(f"✅ {script} is executable")
            else:
                results["issues"].append(f"⚠️  {script} is not executable")
    
    # Check for configuration files
    config_files = [
        "ci/pipelines", "infra/environments", "k8s/base"
    ]
    
    for config_dir in config_files:
        config_path = project_path / config_dir
        if config_path.exists():
            files = list(config_path.glob("*"))
            if files:
                results["passed_checks"].append(f"✅ {config_dir}/ contains {len(files)} files")
            else:
                results["warnings"].append(f"⚠️  {config_dir}/ is empty")
    
    return results


def _display_validation_results(results: dict) -> None:
    """Display validation results in a formatted way"""
    if results["passed_checks"]:
        console.print("\n[bold green]✅ Passed Checks:[/bold green]")
        for check in results["passed_checks"]:
            console.print(f"  {check}")
    
    if results["warnings"]:
        console.print("\n[bold yellow]⚠️  Warnings:[/bold yellow]")
        for warning in results["warnings"]:
            console.print(f"  {warning}")
    
    if results["issues"]:
        console.print("\n[bold red]❌ Issues:[/bold red]")
        for issue in results["issues"]:
            console.print(f"  {issue}")
    
    if results["critical_issues"]:
        console.print("\n[bold red]🚨 Critical Issues:[/bold red]")
        for issue in results["critical_issues"]:
            console.print(f"  {issue}")


def _fix_project_issues(project_path: Path, issues: list) -> None:
    """Attempt to automatically fix common issues"""
    for issue in issues:
        if "is not executable" in issue:
            script_file = issue.split("⚠️  ")[1].split(" is not executable")[0]
            script_path = project_path / script_file
            try:
                os.chmod(script_path, 0o755)
                console.print(f"[green]✅ Fixed: Made {script_file} executable[/green]")
            except Exception as e:
                console.print(f"[red]❌ Could not fix {script_file}: {str(e)}[/red]")
        
        elif "Missing" in issue and "directory" in issue:
            dir_name = issue.split("Missing ")[1].split("/ directory")[0]
            dir_path = project_path / dir_name
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]✅ Fixed: Created {dir_name}/ directory[/green]")
            except Exception as e:
                console.print(f"[red]❌ Could not create {dir_name}/: {str(e)}[/red]")


def _analyze_project(project_path: Path, detailed: bool) -> dict:
    """Analyze the project and return comprehensive statistics"""
    from ..utils import categorize_file, calculate_devops_score, generate_recommendations
    
    stats = {
        "project_name": project_path.name,
        "project_path": project_path,
        "total_size": 0,
        "file_count": 0,
        "directory_count": 0,
        "components": {
            "ci_cd": {"files": [], "size": 0, "platforms": []},
            "infrastructure": {"files": [], "size": 0, "tools": []},
            "deployment": {"files": [], "size": 0, "methods": []},
            "monitoring": {"files": [], "size": 0, "types": []},
            "security": {"files": [], "size": 0, "levels": []},
            "containers": {"files": [], "size": 0},
            "kubernetes": {"files": [], "size": 0},
            "scripts": {"files": [], "size": 0},
        },
        "languages": {},
        "file_types": {},
        "largest_files": [],
        "recent_files": [],
        "devops_score": 0,
        "recommendations": []
    }
    
    try:
        # Analyze all files and directories
        for item in project_path.rglob("*"):
            if item.is_file():
                file_size = item.stat().st_size
                relative_path = item.relative_to(project_path)
                file_ext = item.suffix.lower()
                
                stats["file_count"] += 1
                stats["total_size"] += file_size
                
                # Track file types
                if file_ext:
                    stats["file_types"][file_ext] = stats["file_types"].get(file_ext, 0) + 1
                
                # Track programming languages
                if file_ext in [".py", ".js", ".ts", ".go", ".java", ".rs", ".rb", ".php"]:
                    stats["languages"][file_ext] = stats["languages"].get(file_ext, 0) + 1
                
                # Categorize DevOps components
                category = categorize_file(relative_path)
                if category:
                    comp = stats["components"][category]
                    comp["files"].append(relative_path)
                    comp["size"] += file_size
                    
                    # Extract specific tool/platform info
                    if category == "ci_cd":
                        if "github" in str(relative_path).lower():
                            comp["platforms"].append("GitHub Actions")
                        elif "gitlab" in str(relative_path).lower():
                            comp["platforms"].append("GitLab CI")
                        elif "jenkins" in str(relative_path).lower():
                            comp["platforms"].append("Jenkins")
                    
                    elif category == "infrastructure":
                        if "terraform" in str(relative_path).lower():
                            comp["tools"].append("Terraform")
                        elif "cloudformation" in str(relative_path).lower():
                            comp["tools"].append("CloudFormation")
                    
                    elif category == "deployment":
                        if "docker" in str(relative_path).lower():
                            comp["methods"].append("Docker")
                        elif "k8s" in str(relative_path).lower() or "kubernetes" in str(relative_path).lower():
                            comp["methods"].append("Kubernetes")
                
                # Track largest files
                if len(stats["largest_files"]) < 10:
                    stats["largest_files"].append((relative_path, file_size))
                else:
                    stats["largest_files"].sort(key=lambda x: x[1], reverse=True)
                    if file_size > stats["largest_files"][-1][1]:
                        stats["largest_files"][-1] = (relative_path, file_size)
                
                # Track recent files (by modification time)
                if len(stats["recent_files"]) < 10:
                    stats["recent_files"].append((relative_path, item.stat().st_mtime))
                else:
                    stats["recent_files"].sort(key=lambda x: x[1], reverse=True)
                    if item.stat().st_mtime > stats["recent_files"][-1][1]:
                        stats["recent_files"][-1] = (relative_path, item.stat().st_mtime)
            
            elif item.is_dir() and item != project_path:
                stats["directory_count"] += 1
        
        # Calculate DevOps maturity score
        stats["devops_score"] = calculate_devops_score(stats["components"])
        
        # Generate recommendations
        stats["recommendations"] = generate_recommendations(stats)
        
        # Sort lists for display
        stats["largest_files"].sort(key=lambda x: x[1], reverse=True)
        stats["recent_files"].sort(key=lambda x: x[1], reverse=True)
    
    except Exception as e:
        console.print(f"[yellow]⚠️  Error analyzing project: {str(e)}[/yellow]")
    
    return stats


def _display_project_info(stats: dict, detailed: bool) -> None:
    """Display comprehensive project information"""
    # Basic stats
    console.print(f"\n[bold]📋 Project Overview:[/bold]")
    console.print(f"  Name: {stats['project_name']}")
    console.print(f"  Path: {stats['project_path']}")
    console.print(f"  Size: {stats['total_size'] / (1024*1024):.2f} MB")
    console.print(f"  Files: {stats['file_count']}")
    console.print(f"  Directories: {stats['directory_count']}")
    console.print(f"  DevOps Maturity Score: {stats['devops_score']}/100")
    
    # DevOps components
    console.print(f"\n[bold]🔧 DevOps Components:[/bold]")
    for comp_name, comp_data in stats["components"].items():
        if comp_data["files"]:
            comp_display = comp_name.replace("_", "-").title()
            console.print(f"  {comp_display}: {len(comp_data['files'])} files ({comp_data['size'] / 1024:.1f} KB)")
            
            # Show specific tools/platforms
            if comp_name == "ci_cd" and comp_data["platforms"]:
                platforms = list(set(comp_data["platforms"]))
                console.print(f"    Platforms: {', '.join(platforms)}")
            elif comp_name == "infrastructure" and comp_data["tools"]:
                tools = list(set(comp_data["tools"]))
                console.print(f"    Tools: {', '.join(tools)}")
            elif comp_name == "deployment" and comp_data["methods"]:
                methods = list(set(comp_data["methods"]))
                console.print(f"    Methods: {', '.join(methods)}")
    
    # Languages and file types
    if stats["languages"]:
        console.print(f"\n[bold]💻 Programming Languages:[/bold]")
        for lang, count in sorted(stats["languages"].items(), key=lambda x: x[1], reverse=True):
            lang_name = lang[1:].upper()  # Remove dot and capitalize
            console.print(f"  {lang_name}: {count} files")
    
    if stats["file_types"]:
        console.print(f"\n[bold]📄 File Types:[/bold]")
        for ftype, count in sorted(stats["file_types"].items(), key=lambda x: x[1], reverse=True)[:10]:
            console.print(f"  {ftype or 'no extension'}: {count} files")
    
    # Recommendations
    if stats["recommendations"]:
        console.print(f"\n[bold]💡 Recommendations:[/bold]")
        for rec in stats["recommendations"]:
            console.print(f"  {rec}")
    
    # Detailed analysis
    if detailed:
        console.print(f"\n[bold]🔍 Detailed Analysis:[/bold]")
        
        if stats["largest_files"]:
            console.print(f"\n[dim]Largest files:[/dim]")
            for file_path, size in stats["largest_files"][:5]:
                console.print(f"  {file_path} ({size / 1024:.1f} KB)")
        
        if stats["recent_files"]:
            console.print(f"\n[dim]Recently modified files:[/dim]")
            for file_path, mtime in stats["recent_files"][:5]:
                import datetime
                mod_time = datetime.datetime.fromtimestamp(mtime)
                console.print(f"  {file_path} ({mod_time.strftime('%Y-%m-%d %H:%M')})")


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
        "required_dirs": ["app", "scripts", "docs"],
        "required_files": ["README.md", "Makefile", ".gitignore"],
        "recommended_dirs": ["tests", "config"],
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
    security_dir = project_path / 'security'
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


def _get_project_info(project_path: Path) -> dict:
    """Gather information about the project"""
    info = {
        "name": project_path.name,
        "path": project_path,
        "size_bytes": 0,
        "file_count": 0,
        "dir_count": 0,
        "devops_files": [],
        "config_files": []
    }
    
    try:
        for item in project_path.rglob("*"):
            if item.is_file():
                info["file_count"] += 1
                info["size_bytes"] += item.stat().st_size
                
                # Check for DevOps-specific files
                if any(pattern in str(item) for pattern in ["Dockerfile", "Makefile", ".yml", ".yaml", ".tf", "k8s"]):
                    info["devops_files"].append(item.relative_to(project_path))
                
                # Check for config files
                if item.name.endswith((".yaml", ".yml", ".json", ".toml", ".ini")):
                    info["config_files"].append(item.relative_to(project_path))
            
            elif item.is_dir() and item != project_path:
                info["dir_count"] += 1
    
    except Exception as e:
        console.print(f"[yellow]⚠️  Could not analyze project: {str(e)}[/yellow]")
    
    return info


def _display_project_summary(info: dict) -> None:
    """Display a summary of the project to be cleaned up"""
    size_mb = info["size_bytes"] / (1024 * 1024)
    
    console.print(f"\n[bold]📊 Project Summary:[/bold]")
    console.print(f"  Name: {info['name']}")
    console.print(f"  Path: {info['path']}")
    console.print(f"  Size: {size_mb:.2f} MB")
    console.print(f"  Files: {info['file_count']}")
    console.print(f"  Directories: {info['dir_count']}")
    console.print(f"  DevOps files: {len(info['devops_files'])}")
    console.print(f"  Config files: {len(info['config_files'])}")
    
    if info["devops_files"]:
        console.print(f"\n[dim]DevOps files found:[/dim]")
        for file in info["devops_files"][:10]:  # Show first 10
            console.print(f"  • {file}")
        if len(info["devops_files"]) > 10:
            console.print(f"  ... and {len(info['devops_files']) - 10} more")


def _cleanup_project(project_path: Path, keep_config: bool) -> dict:
    """Perform the actual cleanup operation"""
    import shutil
    
    results = {
        "deleted_files": 0,
        "deleted_dirs": 0,
        "kept_files": [],
        "errors": []
    }
    
    try:
        if keep_config:
            # Preserve config files
            config_files = []
            for item in project_path.rglob("*"):
                if item.is_file() and item.name.endswith((".yaml", ".yml", ".json", ".toml", ".ini")):
                    config_files.append(item)
            
            # Move config files to temporary location
            temp_dir = project_path.parent / f"{project_path.name}_config_backup"
            temp_dir.mkdir(exist_ok=True)
            
            for config_file in config_files:
                try:
                    relative_path = config_file.relative_to(project_path)
                    backup_path = temp_dir / relative_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(config_file), str(backup_path))
                    results["kept_files"].append(str(relative_path))
                except Exception as e:
                    results["errors"].append(f"Could not backup {config_file}: {str(e)}")
        
        # Remove the project directory
        shutil.rmtree(project_path)
        results["deleted_dirs"] = 1  # The main project directory
        
        # Restore config files if they were kept
        if keep_config and results["kept_files"]:
            console.print(f"[yellow]📁 Configuration files backed up to: {temp_dir}[/yellow]")
    
    except Exception as e:
        results["errors"].append(f"Cleanup error: {str(e)}")
    
    return results


def _display_cleanup_results(results: dict) -> None:
    """Display the results of the cleanup operation"""
    if results["errors"]:
        console.print("\n[red]❌ Cleanup completed with errors:[/red]")
        for error in results["errors"]:
            console.print(f"  • {error}")
    else:
        console.print("\n[green]✅ Cleanup completed successfully![/green]")
        console.print(f"  Deleted directories: {results['deleted_dirs']}")
        
        if results["kept_files"]:
            console.print(f"  Preserved config files: {len(results['kept_files'])}")
            for file in results["kept_files"]:
                console.print(f"    • {file}")
