# Changelog

All notable changes to the Claude Documentation Mirror project.

## [1.0.0] - 2025-10-02

### Breaking Changes
- **Installation path changed**: `~/.claude-code-docs` → `~/.claude-docs`
  - Installer auto-migrates existing installations
  - No manual action required
- **Repository renamed**: `ericbuess/claude-code-docs` → `kreitter/claude-docs`
  - Reflects comprehensive scope (CLI + API docs)
  - Fork of original project with enhancements

### Added
- **Comprehensive documentation scope** clearly documented:
  - 38 Claude Code CLI docs (from llms.txt)
  - 76+ API/general docs (from sitemap)
  - 2 other docs (changelog, release notes)
  - Total: 116 files
- **Better discovery logging**: Separate counts for llms.txt and sitemap sources
- **Upstream attribution**: Credit to ericbuess/claude-code-docs
- **Enhanced migration support**: Detects both old and new installation paths

### Changed
- **Python variable names** for accuracy:
  - `discover_claude_code_pages()` → `discover_docs_from_sitemap()`
  - `discover_claude_code_pages_from_llms_txt()` → `discover_claude_code_cli_docs()`
  - `claude_code_pages` → `claude_code_cli_docs` (CLI-specific from llms.txt)
  - `api_pages` → `general_docs` (from sitemap)
  - `documentation_pages` → `all_docs` (combined result)
- **Branding**: "Claude Code Documentation" → "Claude Documentation Mirror"
- **All installation paths**: `~/.claude-code-docs` → `~/.claude-docs`
- **All repository URLs**: `ericbuess/claude-code-docs` → `kreitter/claude-docs`
- **Version alignment**: Scripts now show v1.0.0 consistently

### Fixed
- **Critical installer bug**: No longer deletes development repositories
  - Removed check for current directory in `find_existing_installations()`
  - Only migrates from known installation paths
- **Uninstaller improvements**:
  - Supports both old (`claude-code-docs`) and new (`claude-docs`) patterns
  - Fixed bash scope bug (`local` used outside function)
  - Uses optional chaining for safe jq operations
- **macOS compatibility**:
  - jq commands use optional chaining (`?.`) to handle empty arrays
  - Hook removal works with both old and new naming patterns
- **Naming consistency**: All variables, paths, and URLs now accurately reflect scope

### Migration Notes
- **Automatic migration**: Installer detects v0.3.x installations and auto-migrates
- **Zero downtime**: Migration preserves all documentation and settings
- **Backward compatible**: Uninstaller can remove both old and new versions
- **Safe handling**: Preserves installations with uncommitted changes

### Technical Details
- **fetch_tool_version**: 3.2 → 1.0.0
- **Installation detection**: Enhanced to find both claude-code-docs and claude-docs
- **Hook management**: Safe removal of both old and new hook patterns
- **Upstream**: Fork of [ericbuess/claude-code-docs](https://github.com/ericbuess/claude-code-docs)

---

For older changes, see the [original repository](https://github.com/ericbuess/claude-code-docs/commits/main).
