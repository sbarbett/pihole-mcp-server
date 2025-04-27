# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-04-27

### Added
- New DNS management tools:
  - `add_local_a_record`: Add local A records to Pi-hole
  - `add_local_cname_record`: Add local CNAME records to Pi-hole
  - `remove_local_a_record`: Delete all A records for a hostname with confirmation
  - `remove_local_cname_record`: Delete all CNAME records for a hostname with confirmation
- Token-based confirmation system for DNS deletion operations:
  - First request returns a preview of changes and a unique confirmation token
  - Actual deletion requires the exact confirmation token to proceed
  - Tokens expire after 10 minutes for security
  - Prevents LLM assistants from bypassing confirmation workflow
  - Prevents accidental data removal
  - Removal functions identify all records matching a hostname
  - By default, operations apply to all configured Pi-holes unless a specific one is specified
- Added discovery resource for information on available tools
- Improved docstrings for query functions to better document API usage
- Added MCP prompt guide for LLMs to ensure proper usage of deletion confirmation workflow
  - Detailed instructions on the token-based deletion process
  - Examples of correct and incorrect usage patterns
  - Automatic tool triggers for common user requests
- Added resource and prompt descriptions, and FastMCP instructions

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