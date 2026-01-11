import argparse
import sys
from app.favorites.commands.favorites_to_md import favorites_to_md_command
from app.favorites.commands.favorites_organize import favorites_organize_command
from app.favorites.commands.favorites_deduplicate import favorites_deduplicate_command

def main():
    parser = argparse.ArgumentParser(
        prog="atarax",
        description="Atarax CLI - Main entry point for various modules.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Subparsers for different modules
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Favorites favorites-to-md command
    favorites_to_md_parser = subparsers.add_parser(
        "favorites-to-md",
        help="Convert a Chrome favorites HTML file to various Markdown formats.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Hiérarchie de configuration (priorité décroissante):\n"
               "  1. Arguments CLI (--type, --output, etc.)\n"
               "  2. Fichier YAML (--config)\n"
               "  3. Variables d'environnement (not yet supported for this command)\n"
               "  4. Valeurs par défaut\n\n"
               "Exemples:\n"
               "  # Convertir en arborescence textuelle avec box-drawing characters\n"
               "  atarax favorites-to-md examples\favoris_10_01_2026.html --type monospace -o examples\favoris_10_01_2026.monospace.md\n\n"
               "  # Convertir en PlantUML Tree\n"
               "  atarax favorites-to-md examples\favoris_10_01_2026.html --type tree -o examples\favoris_10_01_2026.tree.puml.md\n\n"
               "  # Afficher l'aide complète\n"
               "  atarax favorites-to-md --help"
    )
    favorites_to_md_parser.add_argument(
        "file_path",
        help="Path to the Chrome favorites HTML file (e.g., examples/favoris_10_01_2026.html)"
    )
    favorites_to_md_parser.add_argument(
        "-o", "--output",
        dest="output_path",
        help="Optional path to save the generated Markdown file. Defaults to <input_file_name>.<type_extension>.md."
    )
    favorites_to_md_parser.add_argument(
        "-t", "--type",
        dest="output_type",
        choices=["monospace", "tree", "mindmap", "mermaid", "stars", "fillers"],
        default="mindmap",
        help="Specify the output format type:\n"
             "  monospace: Textual tree format with box-drawing characters (output will be .monospace.md)\n" 
             "  tree: PlantUML Tree Diagram (output will be .tree.puml.md)\n" 
             "  mindmap: PlantUML Mindmap Diagram (output will be .mindmap.puml.md)\n" 
             "  mermaid: Mermaid Mindmap Diagram (output will be .mermaid.md)\n" 
             "  stars: Textual tree format with stars indicating depth (output will be .stars.md)\n" 
             "  fillers: Textual tree format with '+' characters indicating depth (output will be .fillers.md)"
    )
    favorites_to_md_parser.add_argument(
        "-c", "--config",
        dest="config_path",
        help="Path to a YAML configuration file (not yet implemented)."
    )
    favorites_to_md_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output."
    )
    favorites_to_md_parser.set_defaults(func=lambda args: favorites_to_md_command(
        file_path=args.file_path,
        output_path=args.output_path,
        config_path=args.config_path,
        output_type=args.output_type,
        verbose=args.verbose
    ))

    # Favorites organize command
    favorites_organize_parser = subparsers.add_parser(
        "favorites-organize",
        help="Reorganize browser bookmarks into a clean semantic structure.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Hiérarchie de configuration (priorité décroissante):\n"
               "  1. Arguments CLI (--output, etc.)\n"
               "  2. Fichier YAML (--config)\n"
               "  3. Variables d'environnement (not yet supported for this command)\n"
               "  4. Valeurs par défaut\n\n"
               "Exemples:\n"
               "  # Réorganiser les favoris\n"
               "  atarax favorites-organize examples\\favoris_10_01_2026.html\n\n"
               "  # Spécifier un fichier de sortie\n"
               "  atarax favorites-organize examples\\favoris_10_01_2026.html -o reorganized.html\n\n"
               "  # Afficher l'aide complète\n"
               "  atarax favorites-organize --help"
    )
    favorites_organize_parser.add_argument(
        "input_file",
        help="Input bookmarks HTML file"
    )
    favorites_organize_parser.add_argument(
        "-o", "--output",
        dest="output_file",
        help="Output bookmarks HTML file (default: <input>-reorganized.html)"
    )
    favorites_organize_parser.add_argument(
        "-c", "--config",
        dest="config_path",
        help="Path to a YAML configuration file (not yet implemented)."
    )
    favorites_organize_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output."
    )
    favorites_organize_parser.set_defaults(func=lambda args: favorites_organize_command(
        input_file=args.input_file,
        output_file=args.output_file,
        config_path=args.config_path,
        verbose=args.verbose
    ))

    # Favorites deduplicate command
    favorites_deduplicate_parser = subparsers.add_parser(
        "favorites-deduplicate",
        help="Detect and remove duplicate bookmarks.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Hiérarchie de configuration (priorité décroissante):\n"
               "  1. Arguments CLI (--output, --dry-run, --similarity-threshold)\n"
               "  2. Fichier YAML (--config)\n"
               "  3. Variables d'environnement (not yet supported for this command)\n"
               "  4. Valeurs par défaut\n\n"
               "Exemples:\n"
               "  # Voir les doublons sans modification (dry-run)\n"
               "  atarax favorites-deduplicate examples\\favoris_10_01_2026.html --dry-run -v\n\n"
               "  # Supprimer les doublons\n"
               "  atarax favorites-deduplicate examples\\favoris_10_01_2026.html\n\n"
               "  # Ajuster le seuil de similarité\n"
               "  atarax favorites-deduplicate examples\\favoris_10_01_2026.html --similarity-threshold 0.95\n\n"
               "  # Afficher l'aide complète\n"
               "  atarax favorites-deduplicate --help"
    )
    favorites_deduplicate_parser.add_argument(
        "input_file",
        help="Input bookmarks HTML file"
    )
    favorites_deduplicate_parser.add_argument(
        "-o", "--output",
        dest="output_file",
        help="Output bookmarks HTML file (default: <input>-deduplicated.html)"
    )
    favorites_deduplicate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show duplicates without creating output file"
    )
    favorites_deduplicate_parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.9,
        help="Similarity threshold for title matching (0.0-1.0, default: 0.9)"
    )
    favorites_deduplicate_parser.add_argument(
        "-c", "--config",
        dest="config_path",
        help="Path to a YAML configuration file (not yet implemented)."
    )
    favorites_deduplicate_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output."
    )
    favorites_deduplicate_parser.set_defaults(func=lambda args: favorites_deduplicate_command(
        input_file=args.input_file,
        output_file=args.output_file,
        config_path=args.config_path,
        dry_run=args.dry_run,
        similarity_threshold=args.similarity_threshold,
        verbose=args.verbose
    ))

    args = parser.parse_args()

    if hasattr(args, "func"):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()