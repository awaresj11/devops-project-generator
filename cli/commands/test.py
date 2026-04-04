#!/usr/bin/env python3
"""
Testing commands for DevOps Project Generator
"""

import logging
from pathlib import Path
from typing import Dict, Any

import typer
from rich.console import Console
from rich.panel import Panel

logger = logging.getLogger(__name__)
console = Console()


def test(project_path: str, verbose: bool = False) -> None:
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
