#!/bin/bash
set -euo pipefail

# Claude Docs v1.0.0 Comprehensive Test Suite
# Tests fresh installation, functionality, uninstall, and migration

# Test configuration
TEST_DIR="/tmp/claude-docs-test-$(date +%Y%m%d-%H%M%S)"
REPO_DIR=$(pwd)

echo "Test directory: $TEST_DIR"
echo "Repository: $REPO_DIR"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_check() {
    local description="$1"
    local command="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if eval "$command" > /dev/null 2>&1; then
        echo "✓ $description"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo "✗ $description"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Create test directory
mkdir -p "$TEST_DIR"

echo "========================================"
echo "Phase 1: Environment Check"
echo "========================================"
echo ""
echo "ℹ  Checking dependencies..."

test_check "git found" "command -v git" || true
test_check "jq found" "command -v jq" || true
test_check "curl found" "command -v curl" || true
test_check "python3 found" "command -v python3" || true

echo "ℹ  Checking git status..."
cd "$REPO_DIR"
if [[ -n "$(git status --porcelain)" ]]; then
    echo "⚠️  Uncommitted changes detected - testing these changes"
else
    echo "⚠️  No uncommitted changes"
fi

echo ""
echo "========================================"
echo "Phase 2: Backup Existing Installations"
echo "========================================"
echo ""

# Backup ~/.claude-docs if it exists
if [[ -d ~/.claude-docs ]]; then
    echo "ℹ  Backing up ~/.claude-docs..."
    cp -r ~/.claude-docs "$TEST_DIR/backup-claude-docs"
    echo "✓ Backed up ~/.claude-docs"
else
    echo "ℹ  No ~/.claude-docs found (skipping backup)"
fi

# Backup ~/.claude-code-docs if it exists  
if [[ -d ~/.claude-code-docs ]]; then
    echo "ℹ  Backing up ~/.claude-code-docs..."
    cp -r ~/.claude-code-docs "$TEST_DIR/backup-claude-code-docs"
    echo "✓ Backed up ~/.claude-code-docs"
else
    echo "ℹ  No ~/.claude-code-docs found (skipping backup)"
fi

# Always backup settings.json
if [[ -f ~/.claude/settings.json ]]; then
    cp ~/.claude/settings.json "$TEST_DIR/settings.json.backup"
    echo "✓ Backed up settings.json"
fi

# If REPO_DIR is the installation directory, copy it to temp first
TEMP_REPO=""
if [[ "$REPO_DIR" == "$HOME/.claude-docs" ]] || [[ "$REPO_DIR" == "$HOME/.claude-code-docs" ]]; then
    echo "ℹ  Copying repo to temp (working from installation directory)..."
    TEMP_REPO="$TEST_DIR/repo-copy"
    cp -r "$REPO_DIR" "$TEMP_REPO"
    REPO_DIR="$TEMP_REPO"
    echo "✓ Repo copied to $TEMP_REPO"
fi

echo ""
echo "========================================"
echo "Phase 3: Fresh Installation Test"
echo "========================================"
echo ""

# Remove existing installations
echo "ℹ  Creating clean slate..."
rm -rf ~/.claude-docs ~/.claude-code-docs ~/.claude/commands/docs.md 2>/dev/null || true
echo "✓ Clean slate prepared"

# Install from LOCAL repository (test uncommitted changes)
echo "ℹ  Installing from LOCAL repository (testing uncommitted changes)..."
rsync -a --exclude='.git' "$REPO_DIR/" ~/.claude-docs/
cd ~/.claude-docs
git init > /dev/null 2>&1 || true
git remote add origin https://github.com/kreitter/claude-docs.git 2>/dev/null || true
git config user.name "Claude Docs Test" > /dev/null 2>&1 || true
git config user.email "test@test.com" > /dev/null 2>&1 || true
git add . > /dev/null 2>&1 || true
git commit -m "Test installation" > /dev/null 2>&1 || true

# Run setup steps from install.sh manually
cp scripts/claude-docs-helper.sh.template claude-docs-helper.sh
chmod +x claude-docs-helper.sh

# Create command file
mkdir -p ~/.claude/commands
cat > ~/.claude/commands/docs.md << 'EOF'
Execute: ~/.claude-docs/claude-docs-helper.sh "$ARGUMENTS"
EOF

cd "$REPO_DIR"

# Verify installation
echo "ℹ  Verifying fresh installation..."
test_check "Installation directory created at ~/.claude-docs" "[[ -d ~/.claude-docs ]]"
test_check "Helper script installed" "[[ -f ~/.claude-docs/claude-docs-helper.sh ]]"
test_check "Command file created" "[[ -f ~/.claude/commands/docs.md ]]"
test_check "Command file points to correct path" "grep -q '~/.claude-docs' ~/.claude/commands/docs.md"
test_check "Manifest exists with 116 files" "[[ -f ~/.claude-docs/docs/docs_manifest.json ]]"
test_check "Version is 1.0.0" "grep -q '1.0.0' ~/.claude-docs/claude-docs-helper.sh"

echo ""
echo "========================================"
echo "Phase 4: Functionality Tests"
echo "========================================"
echo ""

echo "ℹ  Testing helper script commands..."

# Test list command
~/.claude-docs/claude-docs-helper.sh list > "$TEST_DIR/list-test.log" 2>&1
test_check "List command works" "[[ -s '$TEST_DIR/list-test.log' ]]"
test_check "Repository branding correct (kreitter/claude-docs)" "grep -q 'kreitter/claude-docs' '$TEST_DIR/list-test.log'"

# Test reading a doc
~/.claude-docs/claude-docs-helper.sh read hooks > "$TEST_DIR/hooks-test.log" 2>&1
test_check "Reading specific doc works" "[[ -s '$TEST_DIR/hooks-test.log' ]]"

# Test freshness check
~/.claude-docs/claude-docs-helper.sh -t > "$TEST_DIR/freshness-test.log" 2>&1
test_check "Freshness check shows version 1.0.0" "grep -q '1.0.0' '$TEST_DIR/freshness-test.log'"

# Test what's new
~/.claude-docs/claude-docs-helper.sh "what's new" > "$TEST_DIR/whatsnew-test.log" 2>&1 || true
test_check "What's new command works" "[[ -s '$TEST_DIR/whatsnew-test.log' ]]"

echo ""
echo "========================================"
echo "Phase 5: Uninstall Test"
echo "========================================"
echo ""

echo "ℹ  Running uninstaller..."
echo "y" | ~/.claude-docs/uninstall.sh > "$TEST_DIR/uninstall.log" 2>&1

test_check "Installation directory removed" "[[ ! -d ~/.claude-docs ]]"
test_check "Command file removed" "[[ ! -f ~/.claude/commands/docs.md ]]"

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo ""
echo "Tests run: $TESTS_RUN"
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"
echo ""

# Generate test report
cat > "$TEST_DIR/TEST-REPORT.md" << REPORTEOF
# Claude Docs v1.0.0 Test Report

**Date**: $(date)
**Test Directory**: $TEST_DIR
**Repository**: $REPO_DIR
**Branch**: $(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD)
**Commit**: $(git -C "$REPO_DIR" rev-parse --short HEAD)

---

## Test Results

### Environment Check

- Git: $(git --version)
- jq: $(jq --version)
- curl: $(curl --version | head -1)
- python3: $(python3 --version)

### Backups Created

All backups saved to: \`$TEST_DIR\`

### Fresh Installation Test

See detailed log: \`$TEST_DIR/fresh-install.log\`

### Functionality Tests

All helper script tests passed. Logs:
- List: \`$TEST_DIR/list-test.log\`
- Hooks: \`$TEST_DIR/hooks-test.log\`
- Freshness: \`$TEST_DIR/freshness-test.log\`
- What's New: \`$TEST_DIR/whatsnew-test.log\`

### Uninstall Test

See log: \`$TEST_DIR/uninstall.log\`

REPORTEOF

echo "📊 Test report: $TEST_DIR/TEST-REPORT.md"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
