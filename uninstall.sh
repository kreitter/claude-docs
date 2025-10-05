#!/bin/bash
set -euo pipefail

# Claude Documentation Mirror - Smart Uninstaller
# Dynamically finds and removes all installations (v0.3.x and v1.0.0+)

echo "Claude Documentation Mirror - Uninstaller"
echo "========================================="
echo ""

# Find all installations from configs
find_all_installations() {
    local paths=()

    # Check standard installation paths first (v0.3.x and v1.0.0+)
    [[ -d ~/.claude-docs ]] && paths+=(~/.claude-docs)
    [[ -d ~/.claude-code-docs ]] && paths+=(~/.claude-code-docs)

    # From command file
    if [[ -f ~/.claude/commands/docs.md ]]; then
        while IFS= read -r line; do
            if [[ "$line" =~ Execute:.*(claude-code-docs|claude-docs) ]]; then
                # Match both old and new naming
                local path=$(echo "$line" | grep -oE '[^ "]*claude(-code)?-docs[^ "]*' | head -1)
                path="${path/#\~/$HOME}"

                # Get directory part
                if [[ -d "$path" ]]; then
                    paths+=("$path")
                elif [[ -d "$(dirname "$path")" ]]; then
                    local dirname=$(basename "$(dirname "$path")")
                    if [[ "$dirname" == "claude-code-docs" || "$dirname" == "claude-docs" ]]; then
                        paths+=("$(dirname "$path")")
                    fi
                fi
            fi
        done < ~/.claude/commands/docs.md
    fi

    # From hooks
    if [[ -f ~/.claude/settings.json ]]; then
        local hooks=$(jq -r '.hooks.PreToolUse[]?.hooks[]?.command // empty' ~/.claude/settings.json 2>/dev/null)
        while IFS= read -r cmd; do
            if [[ "$cmd" =~ claude-code-docs|claude-docs ]]; then
                # Match both old and new naming
                local found=$(echo "$cmd" | grep -oE '[^ "]*claude(-code)?-docs[^ "]*' || true)
                while IFS= read -r path; do
                    [[ -z "$path" ]] && continue
                    path="${path/#\~/$HOME}"
                    # Clean up path to get the directory
                    if [[ "$path" =~ (.*/(claude-code-docs|claude-docs))(/.*)?$ ]]; then
                        path="${BASH_REMATCH[1]}"
                    fi
                    [[ -d "$path" ]] && paths+=("$path")
                done <<< "$found"
            fi
        done <<< "$hooks"
    fi

    # Deduplicate - handle empty array case
    if [[ ${#paths[@]} -gt 0 ]]; then
        printf '%s\n' "${paths[@]}" | sort -u
    fi
}

# Main uninstall logic
installations=()
while IFS= read -r line; do
    installations+=("$line")
done < <(find_all_installations)

if [[ ${#installations[@]} -gt 0 ]]; then
    echo "Found installations at:"
    for path in "${installations[@]}"; do
        echo "  📁 $path"
    done
    echo ""
fi

echo "This will remove:"
echo "  • The /docs command from ~/.claude/commands/docs.md"
echo "  • All claude-docs hooks from ~/.claude/settings.json"
if [[ ${#installations[@]} -gt 0 ]]; then
    echo "  • Installation directories (if safe to remove)"
fi
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Remove command file
if [[ -f ~/.claude/commands/docs.md ]]; then
    rm -f ~/.claude/commands/docs.md
    echo "✓ Removed /docs command"
fi

# Remove hooks
if [[ -f ~/.claude/settings.json ]]; then
    cp ~/.claude/settings.json ~/.claude/settings.json.backup

    # Remove ALL hooks containing claude-code-docs or claude-docs (all versions)
    jq '.hooks.PreToolUse = [(.hooks.PreToolUse // [])[] | select((.hooks[0]?.command? // "" | contains("claude-code-docs") or contains("claude-docs")) | not)]' ~/.claude/settings.json > ~/.claude/settings.json.tmp
    
    # Clean up empty structures
    jq 'if .hooks.PreToolUse == [] then .hooks |= if . == {PreToolUse: []} then {} else del(.PreToolUse) end else . end | if .hooks == {} then del(.hooks) else . end' ~/.claude/settings.json.tmp > ~/.claude/settings.json.tmp2
    
    mv ~/.claude/settings.json.tmp2 ~/.claude/settings.json
    rm -f ~/.claude/settings.json.tmp
    echo "✓ Removed hooks (backup: ~/.claude/settings.json.backup)"
fi

# Remove directories
if [[ ${#installations[@]} -gt 0 ]]; then
    echo ""
    for path in "${installations[@]}"; do
        if [[ ! -d "$path" ]]; then
            continue
        fi
        
        if [[ -d "$path/.git" ]]; then
            # Save current directory
            CURRENT_DIR=$(pwd)
            cd "$path"
            
            if [[ -z "$(git status --porcelain 2>/dev/null)" ]]; then
                cd "$CURRENT_DIR"
                rm -rf "$path"
                echo "✓ Removed $path (clean git repo)"
            else
                cd "$CURRENT_DIR"
                echo "⚠️  Preserved $path (has uncommitted changes)"
            fi
        else
            echo "⚠️  Preserved $path (not a git repo)"
        fi
    done
fi

echo ""
echo "✅ Uninstall complete!"
echo ""
echo "To reinstall:"
echo "curl -fsSL https://raw.githubusercontent.com/kreitter/claude-docs/main/install.sh | bash"