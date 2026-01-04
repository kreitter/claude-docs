# Claude Documentation Mirror

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/kreitter/claude-docs/releases)
[![Last Update](https://img.shields.io/github/last-commit/kreitter/claude-docs/main.svg?label=docs%20updated)](https://github.com/kreitter/claude-docs/commits/main)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-blue)]()

Local mirror of comprehensive Claude documentation from Anthropic's official sites, updated every 3 hours.

**Documentation Sources:**
- **Claude Code**: https://code.claude.com/docs (Build with Claude Code + Reference docs)
- **Platform**: https://platform.claude.com/docs (API reference, Agent SDK, and more)

**Includes:**
- ~17 Claude Code documentation files (Build with Claude Code + Reference categories)
- ~530 Platform API reference documentation files
- 1 changelog file (from Claude Code GitHub repository)
- **Total: ~550 documentation files**

## 🎉 Version 2.0.0 - Dual-Source Update

**This release includes:**
- 🔄 **New documentation sources**: Now fetches from `code.claude.com` and `platform.claude.com`
- 📚 **Expanded coverage**: Full API reference and Agent SDK documentation
- 🏷️ **Categorized filenames**: `code__bwc__*`, `code__ref__*`, `platform__*` prefixes
- ✅ **Production ready**: Stable, tested, comprehensive documentation coverage

**Migrating from v1.x:**
```bash
curl -fsSL https://raw.githubusercontent.com/kreitter/claude-docs/main/install.sh | bash
```
Your installation will automatically update to the new version. No manual action required.

## Why This Exists

- **Faster access** - Reads from local files instead of fetching from web
- **Automatic updates** - Attempts to stay current with the latest documentation
- **Track changes** - See what changed in docs over time
- **Claude Code changelog** - Quick access to official release notes and version history
- **Better Claude Code integration** - Allows Claude to explore documentation more effectively

## Platform Compatibility

- ✅ **macOS**: Fully supported (tested on macOS 12+)
- ✅ **Linux**: Fully supported (Ubuntu, Debian, Fedora, etc.)
- ⏳ **Windows**: Not yet supported - [contributions welcome](#contributing)!

### Prerequisites

This tool requires the following to be installed:
- **git** - For cloning and updating the repository (usually pre-installed)
- **jq** - For JSON processing in the auto-update hook (pre-installed on macOS; Linux users may need `apt install jq` or `yum install jq`)
- **curl** - For downloading the installation script (usually pre-installed)
- **Claude Code** - Obviously :)

## Installation

Run this single command:

```bash
curl -fsSL https://raw.githubusercontent.com/kreitter/claude-docs/main/install.sh | bash
```

This will:
1. Install to `~/.claude-docs` (auto-migrates from v0.3.x if present)
2. Create the `/docs` slash command to pass arguments to the tool and tell it where to find the docs
3. Set up a 'PreToolUse' 'Read' hook to enable automatic git pull when reading docs from `~/.claude-docs`

**Note**: The command is `/docs (user)` - it will show in your command list with "(user)" after it to indicate it's a user-created command.

## Usage

The `/docs` command provides instant access to documentation with optional freshness checking.

### Default: Lightning-fast access (no checks)
```bash
/docs hooks        # Instantly read hooks documentation
/docs mcp          # Instantly read MCP documentation
/docs memory       # Instantly read memory documentation
```

You'll see: `📚 Reading from local docs (run /docs -t to check freshness)`

### Check documentation sync status with -t flag
```bash
/docs -t           # Show sync status with GitHub
/docs -t hooks     # Check sync status, then read hooks docs
/docs -t mcp       # Check sync status, then read MCP docs
```

### See what's new
```bash
/docs what's new   # Show recent documentation changes with diffs
```

### Read Claude Code changelog
```bash
/docs changelog    # Read official Claude Code release notes and version history
```

The changelog feature fetches the latest release notes directly from the official Claude Code repository, showing you what's new in each version.

### Uninstall
```bash
/docs uninstall    # Get command to remove claude-docs completely
```

### Creative usage examples
```bash
# Natural language queries work great
/docs what environment variables exist and how do I use them?
/docs explain the differences between hooks and MCP

# Check for recent changes
/docs -t what's new in the latest documentation?
/docs changelog    # Check Claude Code release notes

# Search across all docs
/docs find all mentions of authentication
/docs how do I customize Claude Code's behavior?
```

## How Updates Work

The documentation attempts to stay current:
- GitHub Actions runs periodically to fetch new documentation
- When you use `/docs`, it checks for updates
- Updates are pulled when available
- You may see "🔄 Updating documentation..." when this happens

Note: If automatic updates fail, you can always run the installer again to get the latest version.

## Updating from Previous Versions

Regardless of which version you have installed, simply run:

```bash
curl -fsSL https://raw.githubusercontent.com/kreitter/claude-docs/main/install.sh | bash
```

The installer will handle migration and updates automatically.

## Troubleshooting

### Command not found
If `/docs` returns "command not found":
1. Check if the command file exists: `ls ~/.claude/commands/docs.md`
2. Restart Claude Code to reload commands
3. Re-run the installation script

### Documentation not updating
If documentation seems outdated:
1. Run `/docs -t` to check sync status and force an update
2. Manually update: `cd ~/.claude-docs && git pull`
3. Check if GitHub Actions are running: [View Actions](https://github.com/kreitter/claude-docs/actions)

### Installation errors
- **"git/jq/curl not found"**: Install the missing tool first
- **"Failed to clone repository"**: Check your internet connection
- **"Failed to update settings.json"**: Check file permissions on `~/.claude/settings.json`

## Uninstalling

To completely remove the docs integration:

```bash
/docs uninstall
```

Or run:
```bash
~/.claude-docs/uninstall.sh
```

See [UNINSTALL.md](UNINSTALL.md) for manual uninstall instructions.

## Security Notes

- The installer modifies `~/.claude/settings.json` to add an auto-update hook
- The hook only runs `git pull` when reading documentation files
- All operations are limited to the documentation directory
- No data is sent externally - everything is local
- **Repository Trust**: The installer clones from GitHub over HTTPS. For additional security, you can:
  - Fork the repository and install from your own fork
  - Clone manually and run the installer from the local directory
  - Review all code before installation

## What's New

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

### v2.0.0 (Current - Dual-Source Update)
- **New documentation sources**: Fetches from `code.claude.com` and `platform.claude.com`
- **Expanded coverage**: ~550 total files (17 Claude Code + 530 Platform + changelog)
- **Categorized filenames**: `code__bwc__*`, `code__ref__*`, `platform__*` prefixes
- **Removed sitemap dependency**: Uses llms.txt for reliable discovery
- **Production ready**: Stable, tested, ready for daily use

### v1.0.0
- **Comprehensive scope**: 38 CLI docs + 76 API docs = 116 total files
- **Path migration**: Auto-migrates `~/.claude-code-docs` → `~/.claude-docs`
- **Repository**: Now at `kreitter/claude-docs` (fork with enhancements)

### Previous Versions
- v0.3.x: Claude Code CLI docs only, at ericbuess/claude-code-docs
- See upstream: https://github.com/ericbuess/claude-code-docs/commits/main

## Contributing

**Contributions are welcome!** This is a community project and we'd love your help:

- 🪟 **Windows Support**: Want to help add Windows compatibility? [Fork the repository](https://github.com/kreitter/claude-docs/fork) and submit a PR!
- 🐛 **Bug Reports**: Found something not working? [Open an issue](https://github.com/kreitter/claude-docs/issues)
- 💡 **Feature Requests**: Have an idea? [Start a discussion](https://github.com/kreitter/claude-docs/issues)
- 📝 **Documentation**: Help improve docs or add examples

You can also use Claude Code itself to help build features - just fork the repo and let Claude assist you!

## Upstream

This is a fork of [ericbuess/claude-code-docs](https://github.com/ericbuess/claude-code-docs) with the following enhancements:
- Expanded scope to include API documentation
- Enhanced installer with migration support
- Improved error handling and macOS compatibility
- Better naming consistency

## Known Issues

If you find any issues, please [report them](https://github.com/kreitter/claude-docs/issues)!

## License

Documentation content belongs to Anthropic.
This mirror tool is open source - contributions welcome!
