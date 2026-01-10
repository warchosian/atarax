# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-10

### Added
- Initial stable release of atarax project
- Favorites-to-md module for converting Chrome favorites HTML to various formats
- Support for multiple output formats:
  - PlantUML Mindmap (.mindmap.puml.md)
  - PlantUML Tree (.tree.puml.md)
  - Mermaid Mindmap (.mermaid.md)
  - Monospace tree (.monospace.md)
  - Stars tree (.stars.md)
  - Fillers tree (.fillers.md)
- Configuration hierarchy support (CLI > YAML > ENV > Defaults)
- Logging support following GEMINI.md project standards
- Command line interface with argparse
- HTML parser for Chrome favorites bookmarks

### Features
- Sanitization of special characters for Mermaid compatibility
- Automatic output file naming based on format type
- Verbose mode for detailed logging
- Export date extraction from HTML bookmarks
