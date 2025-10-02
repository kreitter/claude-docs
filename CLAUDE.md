# Claude Documentation Mirror

**Project-level instructions for Claude Code** - This file helps Claude understand how this repository works and how to support users.

## Project Overview

This repository provides a local mirror of Claude documentation from https://docs.anthropic.com/, including Claude Code user guides (38 docs) and comprehensive API references (76 docs).

- **Version:** 1.0.0
- **Installation Location:** `~/.claude-docs` (fixed location for all users)
- **Previous Location:** `~/.claude-code-docs` (v0.3.x - auto-migrated)
- **Update Frequency:** GitHub Actions runs every 3 hours to fetch latest docs
- **Platform Support:** macOS and Linux (Windows not yet supported)

## How It Works

### Installation Mechanism
The `install.sh` script:
1. Clones/updates the repo to `~/.claude-docs` (auto-migrates from `~/.claude-code-docs`)
2. Creates `~/.claude/commands/docs.md` slash command
3. Installs `claude-docs-helper.sh` from template
4. Adds PreToolUse hook on Read tool (currently dormant but infrastructure in place)

### The /docs Command
When users run `/docs`, Claude Code:
1. Executes `~/.claude-docs/claude-docs-helper.sh` with arguments
2. The helper script handles ALL functionality:
   - `/docs` → Lists all available documentation topics
   - `/docs <topic>` → Reads specific documentation (auto-updates first)
   - `/docs -t` → Shows sync status with GitHub
   - `/docs -t <topic>` → Checks sync status, then reads topic
   - `/docs what's new` → Shows recent documentation changes with diffs
   - `/docs changelog` → Reads Claude Code release notes
   - `/docs uninstall` → Provides uninstall instructions

**Important:** Claude doesn't directly read the docs - the helper script manages everything including on-demand updates.

### Auto-Update Mechanism
- **On-demand updates**: When users run `/docs <topic>`, helper script checks for updates
- Helper script does git fetch to check for updates (~0.4s)
- Pulls latest changes when GitHub has newer content
- Users see "🔄 Updating documentation..." when this happens
- **Note**: PreToolUse hook is installed but currently dormant (infrastructure in place for future use)

## Repository Structure

```
~/.claude-docs/
├── docs/                          # Documentation markdown files (116 total)
│   ├── docs_manifest.json         # Git-tracked, contains hashes and URLs
│   ├── docs__claude-code__*.md    # Claude Code CLI docs (38 files)
│   ├── api__*.md                  # API reference docs (76 files)
│   ├── release-notes__*.md        # Release notes
│   └── changelog.md               # Claude Code changelog
├── scripts/
│   ├── claude-docs-helper.sh.template  # Template for helper script
│   ├── fetch_claude_docs.py       # GitHub Actions uses this to fetch docs
│   └── requirements.txt           # Python dependencies
├── .github/workflows/
│   └── update-docs.yml            # Runs every 3 hours to update docs
├── install.sh                     # Main installer (handles migrations too)
├── uninstall.sh                   # Complete removal script
├── claude-docs-helper.sh          # Installed from template, handles /docs
├── README.md                      # User-facing documentation
├── CLAUDE.md                      # This file
├── UNINSTALL.md                   # Uninstall instructions
└── CHANGELOG.md                   # Version history

# After installation, also creates:
~/.claude/commands/docs.md         # Slash command that calls helper script
~/.claude/settings.json            # Modified to add PreToolUse hook
```

## Supporting Users

### Common Issues and Solutions

**"Command not found"**
- Check if `~/.claude/commands/docs.md` exists
- Suggest restarting Claude Code to reload commands
- Re-run installer if needed

**"Documentation not updating"**
- Run `/docs -t` to check sync status and force update
- Manual update: `cd ~/.claude-docs && git pull`
- Check GitHub Actions status: https://github.com/kreitter/claude-docs/actions

**"Installation errors"**
- Verify dependencies: git, jq, curl
- Check internet connection
- Check file permissions on `~/.claude/settings.json`

**Multiple installations from old versions**
- Installer auto-migrates from old locations to `~/.claude-docs`
- Old installations (including `~/.claude-code-docs`) are removed if they have no uncommitted changes

### Helping Users Find Documentation

The helper script has intelligent search:
- Users can ask natural language questions: `/docs how do I use hooks?`
- The script extracts keywords and searches for matching topics
- Falls back to listing all topics if no matches found

**Available documentation includes:**
- Claude Code docs: hooks, mcp, memory, settings, etc.
- API documentation: Admin API, Agent SDK, etc.
- Release notes: Claude Code changelog

### Version History Context

- **v1.0.0 (Current):** Production release, renamed to `claude-docs`, path migration to `~/.claude-docs`
- **v0.3.3:** Added changelog integration, fixed macOS compatibility
- **v0.3.2:** Fixed auto-update functionality, improved error recovery
- **v0.3.1:** Migration to fixed `~/.claude-code-docs` location
- **v0.2:** Helper script system introduced
- **v0.1:** Original version with different architecture

## Files to Pay Special Attention To

When working on this project, ultrathink about:

- `@install.sh` - Main installer, handles migrations and updates
- `@README.md` - User-facing documentation and installation instructions
- `@uninstall.sh` - Complete uninstall process
- `@UNINSTALL.md` - Manual uninstall instructions
- `@scripts/claude-docs-helper.sh.template` - Core functionality for /docs command
- `@scripts/fetch_claude_docs.py` - Documentation fetching logic
- `@.github/workflows/update-docs.yml` - Auto-update schedule and process

## Important Notes for Claude

1. **Don't read docs directly** - Let the helper script handle it (it manages auto-updates)
2. **The manifest is git-tracked** - It contains hashes and URLs for all docs
3. **Auto-updates are silent** - Unless there are changes to pull
4. **This is a community project** - Not officially affiliated with Anthropic
5. **Production ready** - v1.0.0 is stable for daily use

## Security Considerations

- Installer modifies `~/.claude/settings.json` (adds PreToolUse hook)
- Hook only runs `git pull` when reading documentation files
- All operations limited to documentation directory
- No data sent externally - everything is local
- Repository cloned over HTTPS from GitHub

## Contributing

Users can contribute via:
- Bug reports: https://github.com/kreitter/claude-docs/issues
- Feature requests: GitHub issues
- Pull requests: Fork and submit PRs
- Windows support: Highly desired contribution area

**Upstream**: This is a fork of [ericbuess/claude-code-docs](https://github.com/ericbuess/claude-code-docs) with enhancements.
