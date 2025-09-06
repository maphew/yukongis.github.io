#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "beautifulsoup4>=4.12.0",
#     "lxml>=4.9.0",
# ]
# ///

"""
HTML DOM Sidebar Mover Script

This script scans an HTML document for a section with id "sidebar" and moves it
so it immediately follows the section with id "content".

Usage:
    python move_sidebar.py input.html [output.html]

If no output file is specified, the input file will be modified in place.
"""

import sys
import argparse
from pathlib import Path
from bs4 import BeautifulSoup


def move_sidebar_after_content(html_content: str) -> str:
    """
    Parse HTML and move sidebar section to immediately follow content section.

    Args:
        html_content: Raw HTML content as string

    Returns:
        Modified HTML content with sidebar moved after content

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

    # Remove sidebar from its current position
    sidebar_section.extract()

    # Insert sidebar immediately after content section
    content_section.insert_after(sidebar_section)

    return str(soup)


def main():
    """Main function to handle command line arguments and file operations."""
    parser = argparse.ArgumentParser(
        description="Move HTML sidebar section to follow content section"
    )
    parser.add_argument(
        'input_file',
        type=Path,
        help='Input HTML file to process'
    )
    parser.add_argument(
        'output_file',
        type=Path,
        nargs='?',
        help='Output HTML file (defaults to input file for in-place editing)'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create backup of original file before modifying'
    )

    args = parser.parse_args()

    # Validate input file exists
    if not args.input_file.exists():
        print(f"Error: Input file '{args.input_file}' does not exist", file=sys.stderr)
        sys.exit(1)

    # Set output file (default to input for in-place editing)
    output_file = args.output_file or args.input_file

    try:
        # Read input HTML
        print(f"Reading HTML from: {args.input_file}")
        html_content = args.input_file.read_text(encoding='utf-8')

        # Create backup if requested and doing in-place editing
        if args.backup and output_file == args.input_file:
            backup_file = args.input_file.with_suffix(args.input_file.suffix + '.bak')
            backup_file.write_text(html_content, encoding='utf-8')
            print(f"Backup created: {backup_file}")

        # Process HTML
        print("Moving sidebar section after content section...")
        modified_html = move_sidebar_after_content(html_content)

        # Write output
        output_file.write_text(modified_html, encoding='utf-8')
        print(f"Modified HTML written to: {output_file}")

        print("✅ Successfully moved sidebar after content section")

    except FileNotFoundError:
        print(f"Error: Could not read file '{args.input_file}'", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
