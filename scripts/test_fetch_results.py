#!/usr/bin/env python3
"""
Post-fetch validation tests for claude-docs.

These tests validate that fetch_claude_docs.py ran successfully.
They should FAIL before a fetch and PASS after a successful fetch.

Run with: pytest scripts/test_fetch_results.py -v
"""

import json
import hashlib
import re
from pathlib import Path

import pytest

# Path to docs directory (relative to repo root)
DOCS_DIR = Path(__file__).parent.parent / "docs"
MANIFEST_PATH = DOCS_DIR / "docs_manifest.json"

# Expected Claude Code files (must match hardcoded sets in fetch_claude_docs.py)
EXPECTED_BWC_PAGES = {
    "sub-agents", "plugins", "discover-plugins", "plugin-marketplaces",
    "skills", "output-styles", "hooks-guide", "headless", "mcp",
    "troubleshooting", "devcontainer"
}

EXPECTED_REF_PAGES = {
    "cli-reference", "interactive-mode", "slash-commands", "checkpointing",
    "hooks", "plugins-reference"
}

# Valid domains for documentation URLs (old docs.claude.com should not appear)
VALID_DOMAINS = {"code.claude.com", "platform.claude.com", "github.com", "raw.githubusercontent.com"}


# =============================================================================
# Manifest Tests
# =============================================================================

class TestManifest:
    """Tests for docs_manifest.json existence and structure."""

    def test_manifest_exists(self):
        """Manifest file must exist after fetch."""
        assert MANIFEST_PATH.exists(), f"Manifest not found at {MANIFEST_PATH}"

    def test_manifest_structure(self):
        """Manifest must have required top-level keys."""
        assert MANIFEST_PATH.exists(), "Manifest does not exist"

        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)

        required_keys = {"files", "last_updated", "fetch_metadata"}
        missing_keys = required_keys - set(manifest.keys())
        assert not missing_keys, f"Manifest missing required keys: {missing_keys}"

        # files should be a non-empty dict
        assert isinstance(manifest["files"], dict), "manifest['files'] should be a dict"
        assert len(manifest["files"]) > 0, "manifest['files'] should not be empty"

        # fetch_metadata should exist and have key fields
        metadata = manifest.get("fetch_metadata", {})
        assert "total_files" in metadata, "fetch_metadata missing 'total_files'"
        assert "pages_fetched_successfully" in metadata, "fetch_metadata missing 'pages_fetched_successfully'"

    def test_manifest_urls_use_new_domains(self):
        """All URLs in manifest must use new domains, not old docs.claude.com."""
        assert MANIFEST_PATH.exists(), "Manifest does not exist"

        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)

        invalid_urls = []
        for filename, entry in manifest.get("files", {}).items():
            original_url = entry.get("original_url", "")
            # Check for old domain
            if "docs.claude.com" in original_url and "code.claude.com" not in original_url:
                invalid_urls.append((filename, original_url))

        assert not invalid_urls, f"Found URLs using old docs.claude.com domain: {invalid_urls[:5]}"


# =============================================================================
# Claude Code Documentation Tests
# =============================================================================

class TestClaudeCodeDocs:
    """Tests for Claude Code documentation files (code__bwc__* and code__ref__*)."""

    def test_claude_code_bwc_files_exist(self):
        """All 11 'Build with Claude Code' files must exist."""
        missing = []
        for page in EXPECTED_BWC_PAGES:
            filepath = DOCS_DIR / f"code__bwc__{page}.md"
            if not filepath.exists():
                missing.append(page)

        assert not missing, f"Missing BWC files: {missing}"

    def test_claude_code_ref_files_exist(self):
        """All 6 'Reference' files must exist."""
        missing = []
        for page in EXPECTED_REF_PAGES:
            filepath = DOCS_DIR / f"code__ref__{page}.md"
            if not filepath.exists():
                missing.append(page)

        assert not missing, f"Missing REF files: {missing}"

    def test_claude_code_files_have_content(self):
        """All Claude Code files must be non-empty and contain markdown indicators."""
        empty_files = []
        no_markdown_files = []

        # Check all BWC files
        for page in EXPECTED_BWC_PAGES:
            filepath = DOCS_DIR / f"code__bwc__{page}.md"
            if filepath.exists():
                content = filepath.read_text()
                if len(content) < 100:
                    empty_files.append(str(filepath.name))
                elif not re.search(r'(^#|\*\*|```|\[.*\]\()', content, re.MULTILINE):
                    no_markdown_files.append(str(filepath.name))

        # Check all REF files
        for page in EXPECTED_REF_PAGES:
            filepath = DOCS_DIR / f"code__ref__{page}.md"
            if filepath.exists():
                content = filepath.read_text()
                if len(content) < 100:
                    empty_files.append(str(filepath.name))
                elif not re.search(r'(^#|\*\*|```|\[.*\]\()', content, re.MULTILINE):
                    no_markdown_files.append(str(filepath.name))

        assert not empty_files, f"Files with insufficient content: {empty_files}"
        assert not no_markdown_files, f"Files without markdown indicators: {no_markdown_files}"


# =============================================================================
# Platform Documentation Tests
# =============================================================================

class TestPlatformDocs:
    """Tests for Platform documentation files (platform__*)."""

    def test_platform_files_exist(self):
        """At least 500 platform documentation files must exist."""
        platform_files = list(DOCS_DIR.glob("platform__*.md"))
        count = len(platform_files)

        assert count >= 500, f"Expected at least 500 platform files, found {count}"

    def test_platform_files_naming_pattern(self):
        """All platform files must match the expected naming pattern."""
        platform_files = list(DOCS_DIR.glob("platform__*.md"))

        # Pattern: platform__{path}.md where path uses __ as separator
        invalid_names = []
        for filepath in platform_files:
            name = filepath.name
            # Should start with platform__ and end with .md
            if not name.startswith("platform__") or not name.endswith(".md"):
                invalid_names.append(name)
            # Should not have triple underscores or other anomalies
            elif "___" in name:
                invalid_names.append(name)

        assert not invalid_names, f"Invalid platform file names: {invalid_names[:10]}"


# =============================================================================
# Changelog Test
# =============================================================================

class TestChangelog:
    """Tests for changelog.md file."""

    def test_changelog_exists(self):
        """Changelog must exist and contain version numbers."""
        changelog_path = DOCS_DIR / "changelog.md"

        assert changelog_path.exists(), "changelog.md not found"

        content = changelog_path.read_text()
        assert len(content) > 500, "changelog.md appears to be too short"

        # Should contain version patterns like "1.0.0" or "v1.0.0"
        version_pattern = re.compile(r'\bv?\d+\.\d+\.\d+\b')
        versions = version_pattern.findall(content)

        assert len(versions) >= 5, f"Expected multiple version numbers in changelog, found {len(versions)}"


# =============================================================================
# Integrity Tests
# =============================================================================

class TestIntegrity:
    """Tests for data integrity between manifest and files."""

    def test_manifest_file_hashes_match(self):
        """SHA256 hashes in manifest must match actual file content."""
        assert MANIFEST_PATH.exists(), "Manifest does not exist"

        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)

        mismatches = []
        # Sample 20 files to avoid slow test
        files_to_check = list(manifest.get("files", {}).items())[:20]

        for filename, entry in files_to_check:
            filepath = DOCS_DIR / filename
            if filepath.exists() and "hash" in entry:
                content = filepath.read_bytes()
                actual_hash = hashlib.sha256(content).hexdigest()
                expected_hash = entry["hash"]

                if actual_hash != expected_hash:
                    mismatches.append((filename, expected_hash[:12], actual_hash[:12]))

        assert not mismatches, f"Hash mismatches found: {mismatches}"

    def test_no_orphaned_files(self):
        """Every .md file in docs/ must be referenced in manifest."""
        assert MANIFEST_PATH.exists(), "Manifest does not exist"

        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)

        manifest_files = set(manifest.get("files", {}).keys())
        actual_files = {f.name for f in DOCS_DIR.glob("*.md")}

        orphaned = actual_files - manifest_files

        assert not orphaned, f"Orphaned files not in manifest: {orphaned}"

    def test_no_missing_files(self):
        """Every file in manifest must exist on disk."""
        assert MANIFEST_PATH.exists(), "Manifest does not exist"

        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)

        missing = []
        for filename in manifest.get("files", {}).keys():
            filepath = DOCS_DIR / filename
            if not filepath.exists():
                missing.append(filename)

        assert not missing, f"Files in manifest but missing on disk: {missing[:10]}"


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
