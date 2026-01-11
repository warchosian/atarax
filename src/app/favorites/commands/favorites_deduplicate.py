#!/usr/bin/env python3
import re
import sys
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse, urlunparse
import html
import argparse

# Configure logger
logger = logging.getLogger(__name__)

# -----------------------------
# 1. UTILITY FUNCTIONS
# -----------------------------

def normalize_url(url: str) -> str:
    """
    Normalize URL for comparison.
    - Remove www. prefix
    - Convert to lowercase
    - Remove trailing slash
    - Normalize http/https
    """
    try:
        parsed = urlparse(url.lower())

        # Remove www. from netloc
        netloc = parsed.netloc
        if netloc.startswith('www.'):
            netloc = netloc[4:]

        # Remove trailing slash from path
        path = parsed.path.rstrip('/')

        # Reconstruct URL without scheme (to compare http/https as same)
        normalized = urlunparse(('', netloc, path, parsed.params, parsed.query, parsed.fragment))
        return normalized
    except Exception:
        return url.lower()

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def similarity_ratio(s1: str, s2: str) -> float:
    """
    Calculate similarity ratio between two strings (0.0 to 1.0).
    1.0 means identical, 0.0 means completely different.
    """
    if not s1 or not s2:
        return 0.0

    distance = levenshtein_distance(s1.lower(), s2.lower())
    max_len = max(len(s1), len(s2))

    if max_len == 0:
        return 1.0

    return 1.0 - (distance / max_len)

# -----------------------------
# 2. BOOKMARK CLASS
# -----------------------------

class Bookmark:
    """Represents a bookmark with all its metadata."""

    def __init__(self, url: str, title: str, add_date: str = "", icon: str = ""):
        self.url = url
        self.title = title
        self.add_date = add_date
        self.icon = icon
        self.normalized_url = normalize_url(url)

    def __repr__(self):
        return f"Bookmark(url={self.url[:50]}, title={self.title[:30]})"

    def is_exact_duplicate(self, other: 'Bookmark') -> bool:
        """Check if two bookmarks have identical URLs."""
        return self.url == other.url

    def is_similar_url(self, other: 'Bookmark') -> bool:
        """Check if two bookmarks have similar URLs (normalized)."""
        return self.normalized_url == other.normalized_url

    def title_similarity(self, other: 'Bookmark') -> float:
        """Calculate title similarity ratio."""
        return similarity_ratio(self.title, other.title)

    def is_newer_than(self, other: 'Bookmark') -> bool:
        """Check if this bookmark is newer than another."""
        try:
            if not self.add_date or not other.add_date:
                return False
            return int(self.add_date) > int(other.add_date)
        except (ValueError, TypeError):
            return False

    def has_icon(self) -> bool:
        """Check if bookmark has an icon."""
        return bool(self.icon and self.icon.strip())

# -----------------------------
# 3. DUPLICATE DETECTION
# -----------------------------

def find_duplicates(
    bookmarks: List[Bookmark],
    similarity_threshold: float = 0.9
) -> List[List[Bookmark]]:
    """
    Find duplicate bookmarks.
    Returns a list of duplicate groups.
    Each group contains 2+ bookmarks that are considered duplicates.
    """
    duplicate_groups = []
    processed_indices = set()

    for i, bookmark in enumerate(bookmarks):
        if i in processed_indices:
            continue

        # Find all bookmarks similar to this one
        group = [bookmark]

        for j, other in enumerate(bookmarks[i+1:], start=i+1):
            if j in processed_indices:
                continue

            # Check for duplicates
            is_duplicate = False

            # 1. Exact URL match
            if bookmark.is_exact_duplicate(other):
                is_duplicate = True

            # 2. Similar URL (normalized)
            elif bookmark.is_similar_url(other):
                is_duplicate = True

            # 3. Similar title with same normalized URL
            elif (bookmark.normalized_url == other.normalized_url and
                  bookmark.title_similarity(other) >= similarity_threshold):
                is_duplicate = True

            if is_duplicate:
                group.append(other)
                processed_indices.add(j)

        # Only add groups with duplicates
        if len(group) > 1:
            duplicate_groups.append(group)
            processed_indices.add(i)

    return duplicate_groups

def select_best_bookmark(group: List[Bookmark]) -> Bookmark:
    """
    Select the best bookmark from a group of duplicates.
    Priority:
    1. Most recent (by ADD_DATE)
    2. Has icon
    3. Longest title
    """
    best = group[0]

    for bookmark in group[1:]:
        # Prefer newer
        if bookmark.is_newer_than(best):
            best = bookmark
        elif not best.is_newer_than(bookmark):
            # If same age or no dates, prefer with icon
            if bookmark.has_icon() and not best.has_icon():
                best = bookmark
            elif bookmark.has_icon() == best.has_icon():
                # If same icon status, prefer longest title
                if len(bookmark.title) > len(best.title):
                    best = bookmark

    return best

# -----------------------------
# 4. HTML PARSING AND GENERATION
# -----------------------------

def parse_bookmarks_from_html(file_path: str) -> List[Bookmark]:
    """Parse bookmarks from HTML file."""
    bookmarks = []

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Pattern to match bookmark links
    link_pattern = re.compile(
        r'<DT><A\s+HREF="([^"]*)"(?:\s+ADD_DATE="([^"]*)")?(?:\s+ICON="([^"]*)")?[^>]*>(.*?)</A>',
        re.DOTALL
    )

    for match in link_pattern.finditer(content):
        url = match.group(1)
        add_date = match.group(2) or ""
        icon = match.group(3) or ""
        raw_title = match.group(4) or ""
        title = html.unescape(raw_title.strip())

        bookmark = Bookmark(url, title, add_date, icon)
        bookmarks.append(bookmark)

    return bookmarks

def generate_html_output(
    input_file: str,
    bookmarks_to_keep: List[Bookmark],
    output_file: str
):
    """Generate HTML output with deduplicated bookmarks."""
    # Read original HTML to preserve structure
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Create a set of URLs to keep
    urls_to_keep = {b.url for b in bookmarks_to_keep}

    # Remove duplicate bookmarks from HTML
    def should_keep_bookmark(match):
        url = match.group(1)
        return url in urls_to_keep

    # Pattern to match entire bookmark entry
    link_pattern = re.compile(
        r'<DT><A\s+HREF="([^"]*)"[^>]*>.*?</A>\n?',
        re.DOTALL
    )

    # Track which URLs we've already written
    written_urls = set()

    def replace_bookmark(match):
        url = match.group(1)
        if url in urls_to_keep and url not in written_urls:
            written_urls.add(url)
            return match.group(0)
        return ''

    cleaned_content = link_pattern.sub(replace_bookmark, content)

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

# -----------------------------
# 5. MAIN COMMAND
# -----------------------------

def favorites_deduplicate_command(
    input_file: str,
    output_file: Optional[str] = None,
    config_path: Optional[str] = None,
    dry_run: bool = False,
    similarity_threshold: float = 0.9,
    verbose: bool = False
) -> int:
    """
    Detect and remove duplicate bookmarks.

    Hiérarchie de configuration (du plus au moins prioritaire):
    1. Arguments CLI (input_file, output_file, dry_run, similarity_threshold)
    2. Fichier YAML (config_path) - not yet implemented
    3. Variables d'environnement - not yet implemented
    4. Valeurs par défaut
    """
    if verbose:
        logger.info(f"Deduplicating bookmarks from: {input_file}")

    # Validate input file
    if not os.path.isfile(input_file):
        logger.error(f"Input file '{input_file}' does not exist.")
        return 1

    # Determine output file
    if not output_file:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}-deduplicated.html"
        if verbose:
            logger.info(f"No output file specified. Defaulting to: {output_file}")

    try:
        # Parse bookmarks
        if verbose:
            logger.info("Parsing bookmarks...")
        bookmarks = parse_bookmarks_from_html(input_file)
        total_bookmarks = len(bookmarks)

        if verbose:
            logger.info(f"Found {total_bookmarks} bookmarks")

        # Find duplicates
        if verbose:
            logger.info(f"Detecting duplicates (similarity threshold: {similarity_threshold})...")
        duplicate_groups = find_duplicates(bookmarks, similarity_threshold)

        # Calculate statistics
        total_duplicates = sum(len(group) - 1 for group in duplicate_groups)
        unique_bookmarks = total_bookmarks - total_duplicates

        # Display results
        if dry_run:
            logger.info(f"DRY RUN MODE - No files will be modified")

        logger.info(f"Total bookmarks: {total_bookmarks}")
        logger.info(f"Duplicate groups found: {len(duplicate_groups)}")
        logger.info(f"Total duplicates: {total_duplicates}")
        logger.info(f"Unique bookmarks: {unique_bookmarks}")

        if verbose and duplicate_groups:
            logger.info("\nDuplicate groups:")
            for i, group in enumerate(duplicate_groups, 1):
                logger.info(f"\n  Group {i} ({len(group)} duplicates):")
                for bookmark in group:
                    logger.info(f"    - {bookmark.title[:50]} ({bookmark.url[:60]})")

        if dry_run:
            logger.info(f"\nDry run complete. Run without --dry-run to create: {output_file}")
            return 0

        # Select best bookmark from each group and create deduplicated list
        bookmarks_to_keep = []
        kept_urls = set()

        for group in duplicate_groups:
            best = select_best_bookmark(group)
            if best.url not in kept_urls:
                bookmarks_to_keep.append(best)
                kept_urls.add(best.url)

        # Add non-duplicate bookmarks
        for bookmark in bookmarks:
            if bookmark.url not in kept_urls:
                bookmarks_to_keep.append(bookmark)
                kept_urls.add(bookmark.url)

        # Generate output
        if verbose:
            logger.info(f"Generating deduplicated output...")
        generate_html_output(input_file, bookmarks_to_keep, output_file)

        if verbose:
            logger.info(f"Deduplicated bookmarks saved to: {output_file}")

        # Display only the output file path
        print(output_file)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return 1

def main():
    """Main entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Detect and remove duplicate bookmarks.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input", help="Input bookmarks HTML file")
    parser.add_argument("-o", "--output", help="Output bookmarks HTML file (default: <input>-deduplicated.html)")
    parser.add_argument("--dry-run", action="store_true", help="Show duplicates without creating output file")
    parser.add_argument("--similarity-threshold", type=float, default=0.9,
                       help="Similarity threshold for title matching (0.0-1.0, default: 0.9)")
    parser.add_argument("-c", "--config", dest="config_path", help="Path to YAML configuration file (not yet implemented)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    sys.exit(favorites_deduplicate_command(
        input_file=args.input,
        output_file=args.output,
        config_path=args.config_path,
        dry_run=args.dry_run,
        similarity_threshold=args.similarity_threshold,
        verbose=args.verbose
    ))

if __name__ == "__main__":
    main()
