# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-04-20

### Added
- Enhanced parameters to list_queries for more granular searches
- New metrics endpoints:
  - list_query_history: Returns activity graph data over time
  - list_query_suggestions: Returns filter suggestions for domains, clients, etc.
- Resource that returns the MCP server version (version://)

### Changed
- Restructured project to be more modular for better extensibility
  - Separated tools by functionality (config, metrics)
  - Created dedicated resources directory
  - Updated Docker configuration to support modular structure

### Fixed
- Switched from stdout print statements to stderr logging to prevent interference with STDIO mode

## [0.1.1] - 2025-04-19

### Added
- CHANGELOG.md file
- Support for configuring multiple pi-holes in environment
- Resource for returning pi-hole information
- Development compose file for testing
- Workflow for building and pushing to Docker Hub on release

### Changed
- More graceful session management

## [0.1.0] - 2025-04-18

### Added
- Initial release
- Support for configuring a pi-hole
- Containerization
- List query and list local DNS tools 