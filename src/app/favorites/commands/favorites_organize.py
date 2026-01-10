#!/usr/bin/env python3
import re
import sys
import os
import logging
from collections import defaultdict
from urllib.parse import urlparse
from typing import Optional
import html
import argparse

# Configure logger
logger = logging.getLogger(__name__)

# -----------------------------
# 1. CONFIGURATION : Mapping sémantique
# -----------------------------

CATEGORY_RULES = [
    # Personal > Home & Daily Life
    (["santé", "health", "médecin", "mgen", "alan", "padoa", "tdah", "lyme", "prostate", "cardiac", "cholesterol", "diabetes"], "Personal/Home & Daily Life/Health & Wellness"),
    (["maison", "travaux", "nettoyage", "ménage", "écogest", "énergie", "chèque énergie"], "Personal/Home & Daily Life/Home Management"),
    (["auto", "voiture", "zfe", "vignette", "crit'air", "assurance auto", "tomtom", "waze", "gps"], "Personal/Home & Daily Life/Mobility"),
    (["banque", "la banque postale", "impôts", "fiscalité", "retraite", "succession", "donation", "taxes"], "Personal/Home & Daily Life/Personal Finance"),
    (["cuisine", "nutrition", "jardin", "champignon", "vacances", "bretagne", "montgolfière", "shopping", "fnac", "aliexpress", "rakuten"], "Personal/Home & Daily Life/Leisure & Lifestyle"),

    # Personal > People & Relationships
    (["sandrine", "jessica", "valérie", "daniele", "michel", "fayol", "polizzi", "plotzner"], "Personal/People & Relationships"),

    # Personal > Creativity & Inspiration
    (["rubik", "cube", "sudoku", "jeux", "board game", "deviantart", "pinterest", "suno", "deepart", "musique", "film", "série", "cinéma"], "Personal/Creativity & Inspiration"),

    # Personal > Self-Development
    (["psychologie", "conscience", "rêve lucide", "mbti", "productivité", "mémoire", "philosophie", "épistémologie", "langue", "apprendre l'anglais"], "Personal/Self-Development"),

    # Work > Administration & HR
    (["hr", "rh", "démarches rh", "ensap", "paie", "congés", "télétravail", "présence", "carrière", "formation"], "Work/Administration & HR"),

    # Work > Tools & Enterprise Systems
    (["gitlab", "cerbère", "bastion", "gusi", "sofia", "piag", "resana", "apiop", "vivacite", "pasta", "forge", "redmine", "sg/dnum", "dnum", "snum", "pn m3", "gti", "recette", "eco4", "sireines"], "Work/Tools & Enterprise Systems"),

    # Work > Learning & Skills
    (["devops", "docker", "kubernetes", "jenkins", "ansible", "terraform", "postgresql", "oracle", "python", "java", "typescript", "bash", "sécurité", "urbanisation", "architecture"], "Work/Learning & Skills"),

    # Work > Active Projects
    (["pnm3", "gti", "resana", "glpi", "ticket", "support produit", "doctec", "wikisi"], "Work/Active Projects"),

    # AI & Technology > Artificial Intelligence
    (["claude", "gemini", "gpt", "llama", "mistral", "qwen", "deepseek", "langchain", "rag", "fine-tuning", "prompt", "ollama", "hugging face", "openrouter", "mcp", "agent", "ai coding", "windsurf", "cursor"], "AI & Technology/Artificial Intelligence"),

    # AI & Technology > Computer Science & Development
    (["linux", "wsl", "windows", "ssh", "réseau", "ci/cd", "pipeline", "gradle", "maven", "ant", "groovy", "bonita", "elasticsearch", "kibana", "metabase", "superset", "talend", "grafana", "cloud", "google cloud", "openstack"], "AI & Technology/Computer Science & Development"),

    # AI & Technology > Advanced Sciences & Tech
    (["quantum", "blockchain", "robotique", "aérospatial", "mécanisme", "physique", "biologie", "mathématiques"], "AI & Technology/Advanced Sciences & Tech"),

    # Culture & Knowledge
    (["histoire", "politique", "droit", "économie", "géopolitique", "religion", "mythe", "occultisme", "astronomie", "géologie", "chimie", "écologie", "animaux", "plantes", "microbiote", "art", "littérature", "bd", "manga", "documentaire", "arte", "youtube science"], "Culture & Knowledge"),

    # Practical Utilities
    (["deepl", "google translate", "pdf", "chatpdf", "pdf24", "transcription", "résumé vidéo", "générateur", "prompt", "image generator", "wan ai"], "Practical Utilities"),

    # Quick Access
    (["outlook", "onenote", "passbolt", "bnum", "tchap", "webconférence", "position quotidienne", "daily position"], "Quick Access"),
]

BLACKLISTED_FOLDERS = {"Nouveau dossier", "url", "This", "New", ""}

# -----------------------------
# 2. UTILITAIRES DE PARSING HTML
# -----------------------------

def extract_title_from_url(url):
    parsed = urlparse(url)
    path = parsed.path.strip('/').replace('-', ' ').replace('_', ' ')
    parts = [p.capitalize() for p in path.split('/') if p]
    title = ' / '.join(parts[-2:]) if parts else parsed.netloc
    return title or url

def normalize_title(title):
    if not title or title.strip().lower() in {'url', 'this', 'new'}:
        return None
    title = html.unescape(title.strip())
    title = re.sub(r'^\(\d+\)\s*', '', title)
    return title if title else None

# -----------------------------
# 3. CLASSE POUR LA NOUVELLE ARBORESCENCE
# -----------------------------

class BookmarkNode:
    def __init__(self, name, is_folder=True):
        self.name = name
        self.is_folder = is_folder
        self.url = ""
        self.children = []
        self.add_date = ""
        self.icon = ""

    def add_child(self, child):
        self.children.append(child)

    def find_or_create_path(self, path_parts):
        current = self
        for part in path_parts:
            found = None
            for child in current.children:
                if child.is_folder and child.name == part:
                    found = child
                    break
            if not found:
                found = BookmarkNode(part)
                current.add_child(found)
            current = found
        return current

    def to_html(self, depth=0):
        indent = " " * (depth * 4)
        if not self.is_folder:
            attrs = f' HREF="{self.url}"'
            if self.add_date:
                attrs += f' ADD_DATE="{self.add_date}"'
            if self.icon:
                attrs += f' ICON="{self.icon}"'
            return f'{indent}<DT><A{attrs}>{html.escape(self.name)}</A>\n'
        else:
            html_str = f'{indent}<DT><H3>{html.escape(self.name)}</H3>\n'
            html_str += f'{indent}<DL><p>\n'
            for child in self.children:
                html_str += child.to_html(depth + 1)
            html_str += f'{indent}</DL><p>\n'
            return html_str

# -----------------------------
# 4. FONCTION PRINCIPALE
# -----------------------------

def classify_url(url, title):
    text = (title + " " + url).lower()
    for keywords, target_path in CATEGORY_RULES:
        if any(kw in text for kw in keywords):
            return target_path.split('/')
    domain = urlparse(url).netloc.lower()
    if any(d in domain for d in ['youtube.com', 'youtu.be']):
        return ["Culture & Knowledge", "Arts & Media"]
    if 'gitlab' in domain or 'github.com' in domain:
        return ["AI & Technology", "Computer Science & Development"]
    if 'elastic' in domain or 'kibana' in domain or 'logstash' in domain:
        return ["Work", "Tools & Enterprise Systems"]
    if 'ovh' in domain or 'microsoft.com' in domain or 'stackoverflow.com' in domain:
        return ["AI & Technology", "Computer Science & Development"]
    return ["Culture & Knowledge", "Humanities"]

def favorites_organize_command(
    input_file: str,
    output_file: Optional[str] = None,
    config_path: Optional[str] = None,
    verbose: bool = False
) -> int:
    """
    Reorganize browser bookmarks into a clean semantic structure.

    Hiérarchie de configuration (du plus au moins prioritaire):
    1. Arguments CLI (input_file, output_file)
    2. Fichier YAML (config_path) - not yet implemented
    3. Variables d'environnement - not yet implemented
    4. Valeurs par défaut
    """
    if verbose:
        logger.info(f"Reorganizing bookmarks from: {input_file}")

    if not os.path.isfile(input_file):
        logger.error(f"Input file '{input_file}' does not exist.")
        return 1

    if not output_file:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}-reorganized.html"
        if verbose:
            logger.info(f"No output file specified. Defaulting to: {output_file}")

    try:
        with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        folder_pattern = re.compile(r'<DT><H3[^>]*>(.*?)</H3>')
        link_pattern = re.compile(r'<DT><A\s+HREF="([^"]*)"[^>]*?>(.*?)</A>', re.DOTALL)

        lines = content.splitlines()
        current_path = []
        all_links = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if '<DT><H3' in line:
                match = re.search(r'<DT><H3[^>]*?>(.*?)</H3>', line)
                if match:
                    folder_name = html.unescape(match.group(1))
                    if folder_name not in BLACKLISTED_FOLDERS:
                        current_path.append(folder_name)
            elif '</DL>' in line:
                if current_path:
                    current_path.pop()
            elif '<DT><A HREF=' in line:
                link_match = re.search(r'<DT><A\s+HREF="([^"]*)"(?: ADD_DATE="([^"]*)")?(?: ICON="([^"]*)")?[^>]*>(.*?)</A>', line, re.DOTALL)
                if link_match:
                    url = link_match.group(1)
                    add_date = link_match.group(2) or ""
                    icon = link_match.group(3) or ""
                    raw_title = link_match.group(4) or ""
                    title = normalize_title(raw_title) or extract_title_from_url(url)
                    all_links.append({
                        "url": url,
                        "title": title,
                        "add_date": add_date,
                        "icon": icon,
                        "source_path": list(current_path)
                    })

        seen_urls = set()
        unique_links = []
        for link in all_links:
            if link["url"] not in seen_urls:
                seen_urls.add(link["url"])
                unique_links.append(link)

        root = BookmarkNode("Bookmarks Bar")

        for link in unique_links:
            target_path = classify_url(link["url"], link["title"])
            folder = root.find_or_create_path(target_path)
            leaf = BookmarkNode(link["title"], is_folder=False)
            leaf.url = link["url"]
            leaf.add_date = link["add_date"]
            leaf.icon = link["icon"]
            folder.add_child(leaf)

        header = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>

<DL><p>
"""
        footer = "</DL><p>\n"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(header)
            for child in root.children:
                f.write(child.to_html())
            f.write(footer)

        if verbose:
            logger.info(f"Bookmarks reorganized and saved to: {output_file}")

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
    parser = argparse.ArgumentParser(description="Reorganize browser bookmarks into a clean English structure.")
    parser.add_argument("input", help="Input bookmarks HTML file")
    parser.add_argument("-o", "--output", help="Output bookmarks HTML file (default: <input>-reorganized.html)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    sys.exit(favorites_organize_command(
        input_file=args.input,
        output_file=args.output,
        config_path=None,
        verbose=args.verbose
    ))

if __name__ == "__main__":
    main()