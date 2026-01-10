import argparse
import sys
import os
import datetime
import logging
from pathlib import Path
from typing import Optional, List, Dict, Union, Tuple

from app.favorites.core.parser import parse_favorites_html
from bs4 import BeautifulSoup # Import BeautifulSoup for date extraction

# Configure logger
logger = logging.getLogger(__name__)

# Helper function to parse the date from the HTML header
def _get_export_date(html_content: str) -> str:
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        first_h3 = soup.find('h3')
        if first_h3 and 'ADD_DATE' in first_h3.attrs:
            timestamp = int(first_h3['ADD_DATE'])
            return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
    except (ValueError, AttributeError, TypeError):
        pass # Ignore errors and return default
    return "Unknown Date"

def _format_mindmap_node(node: Union[str, Dict], level: int) -> List[str]:
    """
    Recursively formats the favorites hierarchy into PlantUML Mindmap nodes.
    """
    lines = []
    prefix = '*' * (level + 1) # PlantUML mindmap starts with * for level 1

    if isinstance(node, dict):
        for key, value in node.items():
            if key == 'name' and 'url' in node: # This is a bookmark
                lines.append(f"{prefix} {value} [[{node['url']}]]")
            elif key == 'bookmarks' and isinstance(value, list): # List of bookmarks in a folder
                for bookmark in value:
                    lines.extend(_format_mindmap_node(bookmark, level))
            else: # This is a folder
                lines.append(f"{prefix} {key}")
                if isinstance(value, list):
                    for item in value:
                        lines.extend(_format_mindmap_node(item, level + 1))
                elif isinstance(value, dict): # Should not happen with current parser output, but for safety
                    lines.extend(_format_mindmap_node(value, level + 1))
    elif isinstance(node, list):
        for item in node:
            lines.extend(_format_mindmap_node(item, level))
    
    return lines

def _format_tree_puml_node(node: Union[str, Dict], level: int) -> List[str]:
    """
    Recursively formats the favorites hierarchy into PlantUML Tree nodes.
    """
    lines = []
    prefix = '*' * (level + 1) # PlantUML tree also uses * for levels

    if isinstance(node, dict):
        for key, value in node.items():
            if key == 'name' and 'url' in node: # This is a bookmark
                lines.append(f"{prefix} {value} [[{node['url']}]]")
            elif key == 'bookmarks' and isinstance(value, list): # List of bookmarks in a folder
                for bookmark in value:
                    lines.extend(_format_tree_puml_node(bookmark, level))
            else: # This is a folder
                lines.append(f"{prefix} {key}")
                if isinstance(value, list):
                    for item in value:
                        lines.extend(_format_tree_puml_node(item, level + 1))
                elif isinstance(value, dict):
                    lines.extend(_format_tree_puml_node(value, level + 1))
    elif isinstance(node, list):
        for item in node:
            lines.extend(_format_tree_puml_node(item, level))
            
    return lines

def _format_mermaid_node(node: Union[str, Dict], level: int) -> List[str]:
    """
    Recursively formats the favorites hierarchy into Mermaid Mindmap nodes.
    """
    lines = []
    # Mermaid mindmap uses indentation for hierarchy
    indent = "  " * level

    def sanitize_text(text: str) -> str:
        """Remove or replace problematic characters for Mermaid"""
        # Replace problematic chars with safe alternatives
        text = text.replace('(', '').replace(')', '')
        text = text.replace('[', '').replace(']', '')
        text = text.replace('{', '').replace('}', '')
        text = text.replace('"', '').replace("'", '')
        text = text.replace('`', '').replace('|', '')
        text = text.replace('<', '').replace('>', '')
        # Replace multiple spaces with single space
        text = ' '.join(text.split())
        # Truncate if too long (Mermaid has limits)
        if len(text) > 50:
            text = text[:47] + '...'
        return text.strip()

    if isinstance(node, dict):
        # Check if this is a bookmark first
        if 'name' in node and 'url' in node:
            # This is a bookmark - only output the name
            safe_name = sanitize_text(node['name'])
            lines.append(f'{indent}{safe_name}')
        else:
            # This is a folder - iterate over its contents
            for key, value in node.items():
                if key == 'bookmarks' and isinstance(value, list):
                    # Bookmarks directly under a folder
                    for bookmark in value:
                        lines.extend(_format_mermaid_node(bookmark, level))
                elif key not in ('name', 'url'): # Skip 'name' and 'url' keys
                    safe_key = sanitize_text(key)
                    lines.append(f'{indent}{safe_key}')
                    if isinstance(value, list):
                        for item in value:
                            lines.extend(_format_mermaid_node(item, level + 1))
                    elif isinstance(value, dict):
                        lines.extend(_format_mermaid_node(value, level + 1))
    elif isinstance(node, list):
        for item in node:
            lines.extend(_format_mermaid_node(item, level))

    return lines


def _format_monospace_tree(node: Union[Dict, str], level: int, is_last: bool, indent_prefix: str = "") -> List[str]:
    """
    Recursively formats the favorites hierarchy into a textual tree structure using box-drawing characters.
    Args:
        node: The current node (folder or bookmark) to format.
        level: The current depth level in the tree.
        is_last: True if the current node is the last sibling at its level.
        indent_prefix: The string representing the indentation of parent levels.
    """
    lines = []
    
    # Choose connector based on whether it's the last item
    connector = "└─ " if is_last else "├─ "
    
    if isinstance(node, dict):
        if 'name' in node and 'url' in node: # It's a bookmark
            lines.append(f"{indent_prefix}{connector}{node['name']}")
        else: # It's a folder
            for key, value in node.items():
                if key != 'name' and key != 'url': 
                    lines.append(f"{indent_prefix}{connector}{key}")
                    
                    # Determine next indentation prefix
                    # If current node is last, children get empty space. Otherwise, they get a vertical line.
                    next_indent_prefix = indent_prefix + ("   " if is_last else "│  ")
                    
                    if isinstance(value, list) and value:
                        for i, item in enumerate(value):
                            item_is_last = (i == len(value) - 1)
                            lines.extend(_format_monospace_tree(item, level + 1, item_is_last, next_indent_prefix))
                    elif isinstance(value, dict):
                        lines.extend(_format_monospace_tree(value, level + 1, True, next_indent_prefix))
                elif key == 'bookmarks' and isinstance(value, list):
                    next_indent_prefix = indent_prefix + ("   " if is_last else "│  ")
                    for i, bookmark in enumerate(value):
                        lines.extend(_format_monospace_tree(bookmark, level, i == len(value) - 1, next_indent_prefix))
    elif isinstance(node, list):
        for i, item in enumerate(node):
            lines.extend(_format_monospace_tree(item, level, i == len(node) - 1, indent_prefix))
            
    return lines


def _format_stars_tree(node: Union[Dict, str], level: int) -> List[str]:
    """
    Recursively formats the favorites hierarchy into a stars-based tree structure.
    """
    lines = []
    prefix = '*' * (level + 1) # Use stars for levels

    if isinstance(node, dict):
        for key, value in node.items():
            if key == 'name' and 'url' in node: # This is a bookmark
                lines.append(f"{prefix} {node['name']}")
            elif key == 'bookmarks' and isinstance(value, list): # List of bookmarks in a folder
                for bookmark in value:
                    lines.extend(_format_stars_tree(bookmark, level + 1))
            else: # This is a folder
                lines.append(f"{prefix} {key}")
                if isinstance(value, list):
                    for item in value:
                        lines.extend(_format_stars_tree(item, level + 1))
                elif isinstance(value, dict):
                    lines.extend(_format_stars_tree(value, level + 1))
    elif isinstance(node, list):
        for item in node:
            lines.extend(_format_stars_tree(item, level))
            
    return lines


def _format_fillers_tree(node: Union[Dict, str], level: int) -> List[str]:
    """
    Recursively formats the favorites hierarchy into a fillers-based tree structure using '+' characters.
    """
    lines = []
    prefix = '+' * (level + 1) # Use '+' for levels

    if isinstance(node, dict):
        for key, value in node.items():
            if key == 'name' and 'url' in node: # This is a bookmark
                lines.append(f"{prefix} {node['name']}")
            elif key == 'bookmarks' and isinstance(value, list): # List of bookmarks in a folder
                for bookmark in value:
                    lines.extend(_format_fillers_tree(bookmark, level + 1))
            else: # This is a folder
                lines.append(f"{prefix} {key}")
                if isinstance(value, list):
                    for item in value:
                        lines.extend(_format_fillers_tree(item, level + 1))
                elif isinstance(value, dict):
                    lines.extend(_format_fillers_tree(value, level + 1))
    elif isinstance(node, list):
        for item in node:
            lines.extend(_format_fillers_tree(item, level))
            
    return lines


def favorites_to_md_command(
    file_path: str,
    output_path: Optional[str] = None,
    config_path: Optional[str] = None, # Not used yet, but for config hierarchy
    output_type: str = "mindmap", # Default to mindmap as it's a common output type
    verbose: bool = False
) -> int:
    """
    Convert a Chrome favorites HTML file to various Markdown formats.
    """
    if verbose:
        logger.info(f"Parsing favorites from: {file_path}")

    try:
        # Parse HTML and extract hierarchy
        hierarchy = parse_favorites_html(file_path)

        # Extract date from the HTML file (as it's HTML bookmarks)
        main_date = "Unknown Date"
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            main_date = _get_export_date(html_content)

        input_path_obj = Path(file_path)
        base_name = input_path_obj.stem # Filename without original extension

        # Determine output file path and suffix based on output_type
        if output_path is None:
            if output_type == "monospace":
                output_path = str(input_path_obj.parent / f"{base_name}.monospace.md")
            elif output_type == "tree":
                output_path = str(input_path_obj.parent / f"{base_name}.tree.puml.md")
            elif output_type == "mindmap":
                output_path = str(input_path_obj.parent / f"{base_name}.mindmap.puml.md")
            elif output_type == "mermaid":
                output_path = str(input_path_obj.parent / f"{base_name}.mermaid.md") 
            elif output_type == "stars":
                output_path = str(input_path_obj.parent / f"{base_name}.stars.md")
            elif output_type == "fillers":
                output_path = str(input_path_obj.parent / f"{base_name}.fillers.md")
            else: # Fallback
                output_path = str(input_path_obj.parent / f"{base_name}.md")

            if verbose:
                logger.info(f"No output path specified. Defaulting to: {output_path}")
        else:
            # If output_path is provided, we should ensure its extension is correct based on type
            output_path_obj = Path(output_path)
            if output_type == "monospace" and output_path_obj.suffix.lower() != '.md':
                output_path = str(output_path_obj.with_suffix('.md'))
            elif output_type == "tree" and output_path_obj.suffix.lower() != '.md': # Check for .md as the final extension
                 output_path = str(output_path_obj.with_suffix('.puml.md')) # Ensure both .puml and .md
            elif output_type == "mindmap" and output_path_obj.suffix.lower() != '.md': # Check for .md as the final extension
                 output_path = str(output_path_obj.with_suffix('.puml.md')) # Ensure both .puml and .md
            elif output_type == "mermaid" and output_path_obj.suffix.lower() != '.md':
                 output_path = str(output_path_obj.with_suffix('.md'))
            elif output_type == "stars" and output_path_obj.suffix.lower() != '.md':
                 output_path = str(output_path_obj.with_suffix('.md'))
            elif output_type == "fillers" and output_path_obj.suffix.lower() != '.md':
                 output_path = str(output_path_obj.with_suffix('.md'))

        output_content_lines = []
        
        # Add header with date
        output_content_lines.append(f"# Favorites Hierarchy - Export Date: {main_date}\n")

        if output_type == "monospace":
            # Generate Monospace Textual Tree content
            output_content_lines.append("```text\n") # Use 'text' for generic code block
            output_content_lines.append("# Racine") # Root node for text tree format
            if 'Bookmarks' in hierarchy and isinstance(hierarchy['Bookmarks'], list):
                # The hierarchy's top level contains items (folders or bookmarks)
                for i, item in enumerate(hierarchy['Bookmarks']):
                    output_content_lines.extend(_format_monospace_tree(item, 0, i == len(hierarchy['Bookmarks']) - 1, ""))
            output_content_lines.append("```")
            
        elif output_type == "stars":
            output_content_lines.append("```markdown\n") # Use markdown code block for stars
            output_content_lines.append("# Racine")
            if 'Bookmarks' in hierarchy and isinstance(hierarchy['Bookmarks'], list):
                for i, item in enumerate(hierarchy['Bookmarks']):
                    output_content_lines.extend(_format_stars_tree(item, 0))
            output_content_lines.append("```")

        elif output_type == "fillers":
            output_content_lines.append("```markdown\n") # Use markdown code block for fillers
            output_content_lines.append("# Racine")
            if 'Bookmarks' in hierarchy and isinstance(hierarchy['Bookmarks'], list):
                for i, item in enumerate(hierarchy['Bookmarks']):
                    output_content_lines.extend(_format_fillers_tree(item, 0))
            output_content_lines.append("```")

        elif output_type == "tree": # PlantUML Tree
            output_content_lines.append("```plantuml\n") # PlantUML content in a code block
            output_content_lines.append("@starttree")
            if 'Bookmarks' in hierarchy and isinstance(hierarchy['Bookmarks'], list):
                output_content_lines.append("* Bookmarks") # Root node
                for item in hierarchy['Bookmarks']:
                    output_content_lines.extend(_format_tree_puml_node(item, 1)) # Start children at level 1
            output_content_lines.append("@endtree")
            output_content_lines.append("```")
        
        elif output_type == "mindmap": # PlantUML Mindmap (default)
            output_content_lines.append("```plantuml\n")
            output_content_lines.append("@startmindmap")
            if 'Bookmarks' in hierarchy and isinstance(hierarchy['Bookmarks'], list):
                for item in hierarchy['Bookmarks']:
                    output_content_lines.extend(_format_mindmap_node(item, 1)) # Start children at level 1
            output_content_lines.append("@endmindmap")
            output_content_lines.append("```")

        elif output_type == "mermaid": # Mermaid Mindmap
            output_content_lines.append("```mermaid\n")
            output_content_lines.append("mindmap")
            output_content_lines.append("  root((Bookmarks))") # Mermaid root node (2 spaces)
            if 'Bookmarks' in hierarchy and isinstance(hierarchy['Bookmarks'], list):
                for item in hierarchy['Bookmarks']:
                    output_content_lines.extend(_format_mermaid_node(item, 2)) # Start children at level 2 (4 spaces)
            output_content_lines.append("```")

        else: # Fallback to PlantUML Mindmap
            output_content_lines.append("```plantuml\n")
            output_content_lines.append("@startmindmap")
            if 'Bookmarks' in hierarchy and isinstance(hierarchy['Bookmarks'], list):
                for item in hierarchy['Bookmarks']:
                    output_content_lines.extend(_format_mindmap_node(item, 1)) # Start children at level 1
            output_content_lines.append("@endmindmap")
            output_content_lines.append("```")
        
        output_content = "\n".join(output_content_lines)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)

        if verbose:
            logger.info(f"Successfully converted and saved to: {output_path}")

        # Display only the output file path
        print(output_path)

        return 0
    except FileNotFoundError:
        logger.error(f"Input file not found at {file_path}")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a Chrome favorites HTML file to various Markdown formats.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "file_path",
        help="Path to the Chrome favorites HTML file (e.g., examples/favoris_10_01_2026.html)"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_path",
        help="Optional path to save the generated Markdown file. Defaults to <input_file_name>.<type_extension>.md."
    )
    parser.add_argument(
        "-t", "--type",
        dest="output_type",
        choices=["monospace", "tree", "mindmap", "mermaid", "stars", "fillers"],
        default="mindmap", # Default to mindmap as per current request implies mindmap is preferred graphical
        help="Specify the output format type:\n" 
             "  monospace: Textual tree format with box-drawing characters (output will be .monospace.md)\n" 
             "  tree: PlantUML Tree Diagram (output will be .tree.puml.md)\n" 
             "  mindmap: PlantUML Mindmap Diagram (output will be .mindmap.puml.md)\n" 
             "  mermaid: Mermaid Mindmap Diagram (output will be .mermaid.md)\n" 
             "  stars: Textual tree format with stars indicating depth (output will be .stars.md)\n" 
             "  fillers: Textual tree format with '+' characters indicating depth (output will be .fillers.md)"
    )
    parser.add_argument(
        "-c", "--config",
        dest="config_path",
        help="Path to a YAML configuration file (not yet implemented)."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output."
    )

    args = parser.parse_args()
    sys.exit(
        favorites_to_md_command(
            file_path=args.file_path,
            output_path=args.output_path,
            config_path=args.config_path,
            output_type=args.output_type,
            verbose=args.verbose
        )
    )
