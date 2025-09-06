#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "beautifulsoup4>=4.12.0",
#     "lxml>=4.9.0",
#     "click>=8.0.0",
#     "rich>=13.0.0",
# ]
# ///

"""
HTML DOM Sidebar Mover Script

This script scans HTML documents for a section with id "sidebar" and moves it
so it immediately follows the section with id "content".

Usage:
    python move_sidebar.py input.html              # Single file, dry-run
    python move_sidebar.py --directory ./html/     # All .html files in directory, dry-run
    python move_sidebar.py input.html --execute    # Actually modify the file
"""

import sys
from pathlib import Path
from typing import List, Tuple

import click
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

console = Console()


def move_sidebar_after_content(html_content: str) -> str:
    """
    Parse HTML and move sidebar section to immediately follow content section.
    Also removes aside tags with duplicate IDs and specific unwanted asides within the sidebar section,
    removes script elements with jetpack-*, sharing-js*, comment-reply* IDs and speculationrules type,
    removes iframe with likes-master ID, and removes divs with sharedaddy* classes.

    Args:
        html_content: Raw HTML content as string

    Returns:
        Modified HTML content with sidebar moved after content, duplicate ID asides removed, specific asides removed, unwanted scripts/iframes/divs removed

    Raises:
        ValueError: If required sections are not found
    """
    soup = BeautifulSoup(html_content, 'lxml')

    # Find the content and sidebar sections
    content_section = soup.find(id='content')
    sidebar_section = soup.find(id='sidebar')

    if not content_section:
        raise ValueError("Section with id 'content' not found in HTML")

    if not sidebar_section:
        raise ValueError("Section with id 'sidebar' not found in HTML")

    # Remove unwanted script elements from entire document
    unwanted_scripts = []

    # Find jetpack-* scripts
    jetpack_scripts = soup.find_all('script', id=lambda x: x and x.startswith('jetpack-'))
    unwanted_scripts.extend(jetpack_scripts)

    # Find sharing-js* scripts
    sharing_scripts = soup.find_all('script', id=lambda x: x and x.startswith('sharing-js'))
    unwanted_scripts.extend(sharing_scripts)

    # Find comment-reply* scripts
    comment_scripts = soup.find_all('script', id=lambda x: x and x.startswith('comment-reply'))
    unwanted_scripts.extend(comment_scripts)

    # Find speculationrules scripts
    speculation_scripts = soup.find_all('script', type='speculationrules')
    unwanted_scripts.extend(speculation_scripts)

    scripts_removed = len(unwanted_scripts)
    for script in unwanted_scripts:
        script.decompose()

    # Remove iframe with likes-master ID
    likes_iframe = soup.find('iframe', id='likes-master')
    iframe_removed = 1 if likes_iframe else 0
    if likes_iframe:
        likes_iframe.decompose()

    # Remove divs with sharedaddy* classes
    sharedaddy_divs = soup.find_all('div', class_=lambda x: x and any(cls.startswith('sharedaddy') for cls in x if isinstance(x, list)))
    if not sharedaddy_divs:
        # Also check for single class strings
        sharedaddy_divs = soup.find_all('div', class_=lambda x: isinstance(x, str) and x.startswith('sharedaddy'))

    divs_removed = len(sharedaddy_divs)
    for div in sharedaddy_divs:
        div.decompose()

    # Remove specific unwanted aside tags and duplicate IDs within sidebar
    unwanted_ids = {'search-2', 'meta-2'}
    aside_tags = sidebar_section.find_all('aside', id=True)
    seen_ids = set()
    duplicates_removed = 0
    unwanted_removed = 0

    for aside in aside_tags:
        aside_id = aside.get('id')
        if aside_id in unwanted_ids:
            # This is an unwanted aside, remove it
            aside.decompose()
            unwanted_removed += 1
        elif aside_id in seen_ids:
            # This is a duplicate ID, remove it
            aside.decompose()
            duplicates_removed += 1
        else:
            seen_ids.add(aside_id)

    # Remove sidebar from its current position
    sidebar_section.extract()

    # Insert sidebar immediately after content section
    content_section.insert_after(sidebar_section)

    return str(soup)


def find_html_files(directory: Path) -> List[Path]:
    """Find all .html files in the given directory."""
    html_files = list(directory.glob("*.html"))
    # Also check subdirectories
    html_files.extend(directory.glob("**/*.html"))
    return sorted(set(html_files))  # Remove duplicates and sort


def process_single_file(file_path: Path, backup: bool = False, dry_run: bool = True) -> Tuple[bool, str]:
    """
    Process a single HTML file.

    Returns:
        Tuple of (success, message)
    """
    try:
        html_content = file_path.read_text(encoding='utf-8')

        # Check for duplicate aside IDs, unwanted asides in sidebar, and jetpack scripts before processing
        soup_check = BeautifulSoup(html_content, 'lxml')
        sidebar_check = soup_check.find(id='sidebar')
        duplicate_count = 0
        unwanted_count = 0
        scripts_count = 0
        iframe_count = 0
        divs_count = 0
        unwanted_ids = {'search-2', 'meta-2'}

        # Count unwanted scripts
        unwanted_scripts_check = []
        jetpack_scripts = soup_check.find_all('script', id=lambda x: x and x.startswith('jetpack-'))
        unwanted_scripts_check.extend(jetpack_scripts)
        sharing_scripts = soup_check.find_all('script', id=lambda x: x and x.startswith('sharing-js'))
        unwanted_scripts_check.extend(sharing_scripts)
        comment_scripts = soup_check.find_all('script', id=lambda x: x and x.startswith('comment-reply'))
        unwanted_scripts_check.extend(comment_scripts)
        speculation_scripts = soup_check.find_all('script', type='speculationrules')
        unwanted_scripts_check.extend(speculation_scripts)
        scripts_count = len(unwanted_scripts_check)

        # Count iframe
        likes_iframe = soup_check.find('iframe', id='likes-master')
        iframe_count = 1 if likes_iframe else 0

        # Count sharedaddy divs
        sharedaddy_divs = soup_check.find_all('div', class_=lambda x: x and any(cls.startswith('sharedaddy') for cls in x if isinstance(x, list)))
        if not sharedaddy_divs:
            sharedaddy_divs = soup_check.find_all('div', class_=lambda x: isinstance(x, str) and x.startswith('sharedaddy'))
        divs_count = len(sharedaddy_divs)

        if sidebar_check:
            aside_tags = sidebar_check.find_all('aside', id=True)
            seen_ids = set()
            for aside in aside_tags:
                aside_id = aside.get('id')
                if aside_id in unwanted_ids:
                    unwanted_count += 1
                elif aside_id in seen_ids:
                    duplicate_count += 1
                else:
                    seen_ids.add(aside_id)

        modified_html = move_sidebar_after_content(html_content)

        if dry_run:
            messages = []
            if unwanted_count > 0:
                messages.append(f"would remove {unwanted_count} unwanted asides")
            if duplicate_count > 0:
                messages.append(f"would remove {duplicate_count} duplicate aside IDs")
            if scripts_count > 0:
                messages.append(f"would remove {scripts_count} unwanted scripts")
            if iframe_count > 0:
                messages.append(f"would remove {iframe_count} likes iframe")
            if divs_count > 0:
                messages.append(f"would remove {divs_count} sharedaddy divs")
            detail_msg = f" ({', '.join(messages)})" if messages else ""
            return True, f"Would modify file{detail_msg} (dry-run)"

        # Create backup if requested
        if backup:
            backup_file = file_path.with_suffix(file_path.suffix + '.bak')
            backup_file.write_text(html_content, encoding='utf-8')

        # Write modified content
        file_path.write_text(modified_html, encoding='utf-8')
        backup_msg = " (backup created)" if backup else ""
        messages = []
        if unwanted_count > 0:
            messages.append(f"removed {unwanted_count} unwanted asides")
        if duplicate_count > 0:
            messages.append(f"removed {duplicate_count} duplicate aside IDs")
        if scripts_count > 0:
            messages.append(f"removed {scripts_count} unwanted scripts")
        if iframe_count > 0:
            messages.append(f"removed {iframe_count} likes iframe")
        if divs_count > 0:
            messages.append(f"removed {divs_count} sharedaddy divs")
        detail_msg = f", {', '.join(messages)}" if messages else ""
        return True, f"Successfully modified{backup_msg}{detail_msg}"

    except ValueError as e:
        return False, f"Skip: {e}"
    except Exception as e:
        return False, f"Error: {e}"


@click.command()
@click.argument('input_path', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--directory', '-d',
    is_flag=True,
    help='Process all .html files in the given directory'
)
@click.option(
    '--execute', '-e',
    is_flag=True,
    help='Actually modify files (default is dry-run)'
)
@click.option(
    '--backup', '-b',
    is_flag=True,
    help='Create backup of original files before modifying'
)
@click.option(
    '--confirm/--no-confirm',
    default=True,
    help='Ask for confirmation before processing multiple files'
)
def main(input_path: Path, directory: bool, execute: bool, backup: bool, confirm: bool):
    """
    Move HTML sidebar section to follow content section.

    INPUT_PATH can be either a single .html file or a directory (with --directory flag).
    By default, runs in dry-run mode. Use --execute to actually modify files.
    """

    # Determine files to process
    if directory:
        if not input_path.is_dir():
            console.print(f"[red]Error: {input_path} is not a directory[/red]")
            sys.exit(1)

        html_files = find_html_files(input_path)
        if not html_files:
            console.print(f"[yellow]No .html files found in {input_path}[/yellow]")
            sys.exit(0)

        console.print(f"[blue]Found {len(html_files)} HTML files in {input_path}[/blue]")
    else:
        if input_path.suffix.lower() != '.html':
            console.print(f"[red]Error: {input_path} is not an HTML file[/red]")
            sys.exit(1)
        html_files = [input_path]

    # Show dry-run/execute mode
    mode = "DRY-RUN" if not execute else "EXECUTE"
    mode_color = "yellow" if not execute else "green"
    console.print(Panel(f"Mode: [{mode_color}]{mode}[/{mode_color}]", expand=False))

    if not execute:
        console.print("[yellow]ℹ️  Running in dry-run mode. Use --execute to actually modify files.[/yellow]")

    # Confirm for multiple files
    if len(html_files) > 1 and confirm and execute:
        if not Confirm.ask(f"Process {len(html_files)} files?"):
            console.print("[yellow]Operation cancelled.[/yellow]")
            sys.exit(0)

    # Process files
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:

        task = progress.add_task("Processing files...", total=len(html_files))

        for file_path in html_files:
            progress.update(task, description=f"Processing {file_path.name}")
            success, message = process_single_file(file_path, backup, not execute)
            results.append((file_path, success, message))
            progress.advance(task)

    # Display results
    table = Table(title="Processing Results")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Message")

    success_count = 0
    for file_path, success, message in results:
        status = "✅ Success" if success else "❌ Failed"
        status_color = "green" if success else "red"
        table.add_row(
            str(file_path.relative_to(Path.cwd()) if file_path.is_absolute() else file_path),
            f"[{status_color}]{status}[/{status_color}]",
            message
        )
        if success:
            success_count += 1

    console.print(table)

    # Summary
    total = len(results)
    failed = total - success_count

    if failed == 0:
        console.print(f"[green]🎉 All {total} files processed successfully![/green]")
    else:
        console.print(f"[yellow]⚠️  {success_count}/{total} files processed successfully, {failed} failed/skipped[/yellow]")


if __name__ == '__main__':
    main()
