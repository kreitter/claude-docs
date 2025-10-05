#!/bin/bash
set -e

# Cleanup Script for Claude Docs v1.0.0 Test Artifacts

# macOS uses /private/tmp as the real directory, /tmp is a symlink
# find doesn't follow the /tmp symlink properly, so use the real path
if [[ -d /private/tmp ]]; then
    TMP_DIR="/private/tmp"
else
    TMP_DIR="/tmp"
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Discovery Phase${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Find test directories
TEST_DIRS=()
while IFS= read -r -d '' dir; do
    TEST_DIRS+=("$dir")
done < <(find "$TMP_DIR" -maxdepth 1 -type d -name "claude-docs-test-*" -print0 2>/dev/null | sort -z)

if [ ${#TEST_DIRS[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠️${NC}  No test directories found in $TMP_DIR/"
else
    echo -e "${GREEN}✓${NC} Found ${#TEST_DIRS[@]} test directory(ies):"
    for dir in "${TEST_DIRS[@]}"; do
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1)
        TIMESTAMP=$(basename "$dir" | sed 's/claude-docs-test-//')
        echo "  - $TIMESTAMP ($SIZE)"
    done
fi

echo ""
echo -e "${CYAN}ℹ${NC}  Checking installations..."

# Check for installations
if [[ -d ~/.claude-docs ]]; then
    echo -e "${GREEN}✓${NC} ~/.claude-docs exists"
else
    echo -e "${CYAN}ℹ${NC}  No ~/.claude-docs found"
fi

if [[ -d ~/.claude-code-docs ]]; then
    echo -e "${GREEN}✓${NC} ~/.claude-code-docs exists"
else
    echo -e "${CYAN}ℹ${NC}  No ~/.claude-code-docs found"
fi

echo ""
echo -e "${CYAN}ℹ${NC}  Checking configuration..."
if [[ -f ~/.claude/commands/docs.md ]]; then
    echo -e "${GREEN}✓${NC} /docs command exists"
else
    echo -e "${CYAN}ℹ${NC}  No /docs command found"
fi

if [[ -f ~/.claude/settings.json ]]; then
    HOOK_COUNT=$(grep -c "claude-docs\|claude-code-docs" ~/.claude/settings.json 2>/dev/null || echo "0")
    if [[ $HOOK_COUNT -gt 0 ]]; then
        echo -e "${GREEN}✓${NC} Found $HOOK_COUNT claude-docs hook(s)"
    else
        echo -e "${CYAN}ℹ${NC}  No claude-docs hooks found"
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Clean All Test Artifacts${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${CYAN}ℹ${NC}  Cleanup plan:"
echo ""

if [ ${#TEST_DIRS[@]} -gt 0 ]; then
    echo "Will remove ${#TEST_DIRS[@]} test directory(ies):"
    for dir in "${TEST_DIRS[@]}"; do
        echo "  - $(basename "$dir")"
    done
    echo ""
fi

read -p "Continue? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Executing Cleanup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Remove test directories
if [ ${#TEST_DIRS[@]} -gt 0 ]; then
    echo -e "${CYAN}ℹ${NC}  Removing test directories..."
    for dir in "${TEST_DIRS[@]}"; do
        rm -rf "$dir"
    done
    echo -e "${GREEN}✓${NC} Removed ${#TEST_DIRS[@]} test directory(ies)"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cleanup Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✓${NC} All test artifacts removed"
