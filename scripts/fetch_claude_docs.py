#!/usr/bin/env python3
"""
Improved Claude Code documentation fetcher with better robustness.
"""

import requests
import time
from pathlib import Path
from typing import List, Tuple, Set, Optional
import logging
from datetime import datetime
import sys
from urllib.parse import urlparse
import json
import hashlib
import os
import re
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Documentation sources (new Anthropic structure as of 2025)
CLAUDE_CODE_BASE_URL = "https://code.claude.com/docs"
PLATFORM_BASE_URL = "https://platform.claude.com/docs"

# llms.txt endpoints for document discovery
# NOTE: Platform llms.txt is at root, not under /docs/
LLMS_TXT_URLS = {
    "claude_code": f"{CLAUDE_CODE_BASE_URL}/llms.txt",  # code.claude.com/docs/llms.txt
    "platform": "https://platform.claude.com/llms.txt",  # NOT /docs/llms.txt
}

# Pages under "BUILD WITH CLAUDE CODE" category
BUILD_WITH_CLAUDE_CODE_PAGES = {
    "sub-agents", "plugins", "discover-plugins", "plugin-marketplaces",
    "skills", "output-styles", "hooks-guide", "headless", "mcp",
    "troubleshooting", "devcontainer"
}

# Pages under "REFERENCE" category
REFERENCE_PAGES = {
    "cli-reference", "interactive-mode", "slash-commands", "checkpointing",
    "hooks", "plugins-reference"
}

MANIFEST_FILE = "docs_manifest.json"

# Note: Sitemap-based discovery has been removed in v2.0.0
# All discovery now uses llms.txt from code.claude.com and platform.claude.com

# Headers to bypass caching and identify the script
HEADERS = {
    'User-Agent': 'Claude-Code-Docs-Fetcher/3.0',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # initial delay in seconds
MAX_RETRY_DELAY = 30  # maximum delay in seconds
RATE_LIMIT_DELAY = 0.5  # seconds between requests


def load_manifest(docs_dir: Path) -> dict:
    """Load the manifest of previously fetched files."""
    manifest_path = docs_dir / MANIFEST_FILE
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            # Ensure required keys exist
            if "files" not in manifest:
                manifest["files"] = {}
            return manifest
        except Exception as e:
            logger.warning(f"Failed to load manifest: {e}")
    return {"files": {}, "last_updated": None}


def save_manifest(docs_dir: Path, manifest: dict) -> None:
    """Save the manifest of fetched files."""
    manifest_path = docs_dir / MANIFEST_FILE
    manifest["last_updated"] = datetime.now().isoformat()
    
    # Get GitHub repository from environment or use default
    github_repo = os.environ.get('GITHUB_REPOSITORY', 'kreitter/claude-docs')
    github_ref = os.environ.get('GITHUB_REF_NAME', 'main')

    # Validate repository name format (owner/repo)
    if not re.match(r'^[\w.-]+/[\w.-]+$', github_repo):
        logger.warning(f"Invalid repository format: {github_repo}, using default")
        github_repo = 'kreitter/claude-docs'
    
    # Validate branch/ref name
    if not re.match(r'^[\w.-]+$', github_ref):
        logger.warning(f"Invalid ref format: {github_ref}, using default")
        github_ref = 'main'
    
    manifest["base_url"] = f"https://raw.githubusercontent.com/{github_repo}/{github_ref}/docs/"
    manifest["github_repository"] = github_repo
    manifest["github_ref"] = github_ref
    manifest["description"] = "Claude Code documentation manifest. Keys are filenames, append to base_url for full URL."
    manifest_path.write_text(json.dumps(manifest, indent=2))


def url_to_safe_filename(url_path: str, source: str, category: str = None) -> str:
    """
    Convert URL path to safe filename with source/category prefix.

    Args:
        url_path: The page path (e.g., "hooks", "api/messages.md")
        source: "code" or "platform"
        category: For code.claude.com: "bwc" or "ref" (required)
                  For platform.claude.com: None (not used)

    Examples:
        ("hooks-guide", "code", "bwc") -> code__bwc__hooks-guide.md
        ("hooks", "code", "ref") -> code__ref__hooks.md
        ("api/messages.md", "platform", None) -> platform__api__messages.md
    """
    # Remove .md extension if present (proper suffix removal, not rstrip!)
    path = url_path[:-3] if url_path.endswith('.md') else url_path

    # Clean leading/trailing slashes
    path = path.strip('/')

    # Convert path separators to double underscores
    safe_name = path.replace('/', '__')

    # Build prefix based on source
    if source == "code" and category:
        prefix = f"code__{category}"  # code__bwc or code__ref
    else:
        prefix = source  # platform

    return f"{prefix}__{safe_name}.md"


def discover_claude_code_docs(session: requests.Session) -> List[Tuple[str, str, str]]:
    """
    Discover Claude Code docs from llms.txt and categorize them.
    Returns list of (full_url, page_name, category) tuples.
    Only returns pages in BUILD_WITH_CLAUDE_CODE or REFERENCE categories.
    """
    llms_url = LLMS_TXT_URLS["claude_code"]
    logger.info(f"Discovering Claude Code docs from {llms_url}...")

    try:
        response = session.get(llms_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch Claude Code llms.txt: {e}")
        raise

    # Match: [Title](https://code.claude.com/docs/en/page-name.md)
    pattern = re.compile(r'\[.*?\]\((https://code\.claude\.com/docs/en/([^)]+))\.md\)')

    results = []
    for match in pattern.finditer(response.text):
        full_url = match.group(1) + ".md"  # Reconstruct full URL with .md
        page_name = match.group(2)  # e.g., "hooks", "sub-agents"

        if page_name in BUILD_WITH_CLAUDE_CODE_PAGES:
            results.append((full_url, page_name, "bwc"))
        elif page_name in REFERENCE_PAGES:
            results.append((full_url, page_name, "ref"))
        else:
            # Log unknown pages so we notice when Anthropic adds new docs
            logger.warning(f"Unknown Claude Code page not in any category: {page_name} - add to BUILD_WITH_CLAUDE_CODE_PAGES or REFERENCE_PAGES if needed")

    logger.info(f"Discovered {len(results)} Claude Code docs (BWC + Reference)")
    return results


def discover_platform_docs(session: requests.Session) -> List[Tuple[str, str]]:
    """
    Discover all platform docs from llms.txt.
    Returns list of (full_url, path) tuples.
    """
    llms_url = LLMS_TXT_URLS["platform"]
    logger.info(f"Discovering Platform docs from {llms_url}...")

    try:
        response = session.get(llms_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch Platform llms.txt: {e}")
        raise

    # Match: [Title](https://platform.claude.com/docs/en/path.md)
    pattern = re.compile(r'\[.*?\]\((https://platform\.claude\.com/docs/en/([^)]+\.md))\)')

    results = []
    for match in pattern.finditer(response.text):
        full_url = match.group(1)
        path = match.group(2)  # e.g., "api/messages.md"
        results.append((full_url, path))

    logger.info(f"Discovered {len(results)} Platform docs")
    return results


def validate_markdown_content(content: str, filename: str) -> None:
    """
    Validate that content is proper markdown.
    Raises ValueError if validation fails.
    """
    # Check for HTML content
    if not content or content.startswith('<!DOCTYPE') or '<html' in content[:100]:
        raise ValueError("Received HTML instead of markdown")
    
    # Check minimum length
    if len(content.strip()) < 50:
        raise ValueError(f"Content too short ({len(content)} bytes)")
    
    # Check for common markdown elements
    lines = content.split('\n')
    markdown_indicators = [
        '# ',      # Headers
        '## ',
        '### ',
        '```',     # Code blocks
        '- ',      # Lists
        '* ',
        '1. ',
        '[',       # Links
        '**',      # Bold
        '_',       # Italic
        '> ',      # Quotes
    ]
    
    # Count markdown indicators
    indicator_count = 0
    for line in lines[:50]:  # Check first 50 lines
        for indicator in markdown_indicators:
            if line.strip().startswith(indicator) or indicator in line:
                indicator_count += 1
                break
    
    # Require at least some markdown formatting
    if indicator_count < 3:
        raise ValueError(f"Content doesn't appear to be markdown (only {indicator_count} markdown indicators found)")
    
    # Check for common documentation patterns
    doc_patterns = ['installation', 'usage', 'example', 'api', 'configuration', 'claude', 'code']
    content_lower = content.lower()
    pattern_found = any(pattern in content_lower for pattern in doc_patterns)
    
    if not pattern_found:
        logger.warning(f"Content for {filename} doesn't contain expected documentation patterns")


def fetch_markdown_content(
    markdown_url: str,
    session: requests.Session,
    source: str,
    category: str = None,
    page_path: str = None
) -> Tuple[str, str]:
    """
    Fetch markdown content with better error handling and validation.

    Args:
        markdown_url: Full URL to the markdown file
        session: requests Session object
        source: "code" or "platform"
        category: For code.claude.com: "bwc" or "ref"
        page_path: The path portion for filename generation (e.g., "hooks", "api/messages.md")
    """
    filename = url_to_safe_filename(page_path, source, category)

    logger.info(f"Fetching: {markdown_url} -> {filename}")

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(markdown_url, headers=HEADERS, timeout=30, allow_redirects=True)

            # Handle specific HTTP errors
            if response.status_code == 429:  # Rate limited
                wait_time = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()

            # Get content and validate
            content = response.text
            validate_markdown_content(content, filename)

            logger.info(f"Successfully fetched and validated {filename} ({len(content)} bytes)")
            return filename, content

        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {filename}: {e}")
            if attempt < MAX_RETRIES - 1:
                # Exponential backoff with jitter
                delay = min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                # Add jitter to prevent thundering herd
                jittered_delay = delay * random.uniform(0.5, 1.0)
                logger.info(f"Retrying in {jittered_delay:.1f} seconds...")
                time.sleep(jittered_delay)
            else:
                raise Exception(f"Failed to fetch {filename} after {MAX_RETRIES} attempts: {e}")

        except ValueError as e:
            logger.error(f"Content validation failed for {filename}: {e}")
            raise


def content_has_changed(content: str, old_hash: str) -> bool:
    """Check if content has changed based on hash."""
    new_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    return new_hash != old_hash


def fetch_changelog(session: requests.Session) -> Tuple[str, str]:
    """
    Fetch Claude Code changelog from GitHub repository.
    Returns tuple of (filename, content).
    """
    changelog_url = "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md"
    filename = "changelog.md"
    
    logger.info(f"Fetching Claude Code changelog: {changelog_url}")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(changelog_url, headers=HEADERS, timeout=30, allow_redirects=True)
            
            if response.status_code == 429:  # Rate limited
                wait_time = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            
            content = response.text
            
            # Add header to indicate this is from Claude Code repo, not docs site
            header = """# Claude Code Changelog

> **Source**: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
> 
> This is the official Claude Code release changelog, automatically fetched from the Claude Code repository. For documentation, see other topics via `/docs`.

---

"""
            content = header + content
            
            # Basic validation
            if len(content.strip()) < 100:
                raise ValueError(f"Changelog content too short ({len(content)} bytes)")
            
            logger.info(f"Successfully fetched changelog ({len(content)} bytes)")
            return filename, content
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for changelog: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                jittered_delay = delay * random.uniform(0.5, 1.0)
                logger.info(f"Retrying in {jittered_delay:.1f} seconds...")
                time.sleep(jittered_delay)
            else:
                raise Exception(f"Failed to fetch changelog after {MAX_RETRIES} attempts: {e}")
        
        except ValueError as e:
            logger.error(f"Changelog validation failed: {e}")
            raise


def save_markdown_file(docs_dir: Path, filename: str, content: str) -> str:
    """Save markdown content and return its hash."""
    file_path = docs_dir / filename
    
    try:
        file_path.write_text(content, encoding='utf-8')
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        logger.info(f"Saved: {filename}")
        return content_hash
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}")
        raise


def cleanup_old_files(docs_dir: Path, current_files: Set[str], manifest: dict) -> None:
    """
    Remove only files that were previously fetched but no longer exist.
    Preserves manually added files.
    """
    previous_files = set(manifest.get("files", {}).keys())
    files_to_remove = previous_files - current_files
    
    for filename in files_to_remove:
        if filename == MANIFEST_FILE:  # Never delete the manifest
            continue
            
        file_path = docs_dir / filename
        if file_path.exists():
            logger.info(f"Removing obsolete file: {filename}")
            file_path.unlink()


def main():
    """Main function with dual-source documentation fetching."""
    start_time = datetime.now()
    logger.info("Starting Claude documentation fetch v2.0.0")

    # Log configuration
    github_repo = os.environ.get('GITHUB_REPOSITORY', 'kreitter/claude-docs')
    logger.info(f"GitHub repository: {github_repo}")

    # Create docs directory at repository root
    docs_dir = Path(__file__).parent.parent / 'docs'
    docs_dir.mkdir(exist_ok=True)
    logger.info(f"Output directory: {docs_dir}")

    # Load manifest
    manifest = load_manifest(docs_dir)

    # Statistics
    successful = 0
    failed = 0
    failed_pages = []
    fetched_files = set()
    new_manifest = {"files": {}}
    discovery_methods = []
    total_discovered = 0

    with requests.Session() as session:
        # ============================================================
        # Source 1: Claude Code docs (code.claude.com)
        # Only BWC (Build with Claude Code) and Reference categories
        # ============================================================
        try:
            claude_code_docs = discover_claude_code_docs(session)
            discovery_methods.append(f"code.claude.com({len(claude_code_docs)} pages)")
            total_discovered += len(claude_code_docs)

            for i, (full_url, page_name, category) in enumerate(claude_code_docs, 1):
                logger.info(f"[Claude Code {i}/{len(claude_code_docs)}] {page_name} ({category})")

                try:
                    filename, content = fetch_markdown_content(
                        markdown_url=full_url,
                        session=session,
                        source="code",
                        category=category,
                        page_path=page_name
                    )

                    # Check if content has changed
                    old_hash = manifest.get("files", {}).get(filename, {}).get("hash", "")
                    old_entry = manifest.get("files", {}).get(filename, {})

                    if content_has_changed(content, old_hash):
                        content_hash = save_markdown_file(docs_dir, filename, content)
                        logger.info(f"Updated: {filename}")
                        last_updated = datetime.now().isoformat()
                    else:
                        content_hash = old_hash
                        logger.info(f"Unchanged: {filename}")
                        last_updated = old_entry.get("last_updated", datetime.now().isoformat())

                    new_manifest["files"][filename] = {
                        "original_url": full_url[:-3],  # Remove .md for display URL
                        "original_md_url": full_url,
                        "hash": content_hash,
                        "last_updated": last_updated,
                        "source": "code.claude.com",
                        "category": category
                    }

                    fetched_files.add(filename)
                    successful += 1

                    # Rate limiting
                    time.sleep(RATE_LIMIT_DELAY)

                except Exception as e:
                    logger.error(f"Failed to process {page_name}: {e}")
                    failed += 1
                    failed_pages.append(f"code:{page_name}")

        except Exception as e:
            logger.error(f"Failed to discover Claude Code docs: {e}")

        # ============================================================
        # Source 2: Platform docs (platform.claude.com)
        # All documentation
        # ============================================================
        try:
            platform_docs = discover_platform_docs(session)
            discovery_methods.append(f"platform.claude.com({len(platform_docs)} pages)")
            total_discovered += len(platform_docs)

            for i, (full_url, path) in enumerate(platform_docs, 1):
                logger.info(f"[Platform {i}/{len(platform_docs)}] {path}")

                try:
                    filename, content = fetch_markdown_content(
                        markdown_url=full_url,
                        session=session,
                        source="platform",
                        category=None,
                        page_path=path
                    )

                    # Check if content has changed
                    old_hash = manifest.get("files", {}).get(filename, {}).get("hash", "")
                    old_entry = manifest.get("files", {}).get(filename, {})

                    if content_has_changed(content, old_hash):
                        content_hash = save_markdown_file(docs_dir, filename, content)
                        logger.info(f"Updated: {filename}")
                        last_updated = datetime.now().isoformat()
                    else:
                        content_hash = old_hash
                        logger.info(f"Unchanged: {filename}")
                        last_updated = old_entry.get("last_updated", datetime.now().isoformat())

                    new_manifest["files"][filename] = {
                        "original_url": full_url[:-3],  # Remove .md for display URL
                        "original_md_url": full_url,
                        "hash": content_hash,
                        "last_updated": last_updated,
                        "source": "platform.claude.com"
                    }

                    fetched_files.add(filename)
                    successful += 1

                    # Rate limiting
                    time.sleep(RATE_LIMIT_DELAY)

                except Exception as e:
                    logger.error(f"Failed to process {path}: {e}")
                    failed += 1
                    failed_pages.append(f"platform:{path}")

        except Exception as e:
            logger.error(f"Failed to discover Platform docs: {e}")

        # ============================================================
        # Source 3: Claude Code changelog (GitHub)
        # ============================================================
        logger.info("Fetching Claude Code changelog...")
        try:
            filename, content = fetch_changelog(session)

            # Check if content has changed
            old_hash = manifest.get("files", {}).get(filename, {}).get("hash", "")
            old_entry = manifest.get("files", {}).get(filename, {})

            if content_has_changed(content, old_hash):
                content_hash = save_markdown_file(docs_dir, filename, content)
                logger.info(f"Updated: {filename}")
                last_updated = datetime.now().isoformat()
            else:
                content_hash = old_hash
                logger.info(f"Unchanged: {filename}")
                last_updated = old_entry.get("last_updated", datetime.now().isoformat())

            new_manifest["files"][filename] = {
                "original_url": "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md",
                "original_raw_url": "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md",
                "hash": content_hash,
                "last_updated": last_updated,
                "source": "claude-code-repository"
            }

            fetched_files.add(filename)
            successful += 1

        except Exception as e:
            logger.error(f"Failed to fetch changelog: {e}")
            failed += 1
            failed_pages.append("changelog")

    # Clean up old files (only those we previously fetched)
    cleanup_old_files(docs_dir, fetched_files, manifest)

    # Add metadata to manifest
    new_manifest["fetch_metadata"] = {
        "last_fetch_completed": datetime.now().isoformat(),
        "fetch_duration_seconds": (datetime.now() - start_time).total_seconds(),
        "total_pages_discovered": total_discovered,
        "pages_fetched_successfully": successful,
        "pages_failed": failed,
        "failed_pages": failed_pages,
        "discovery_methods": discovery_methods,
        "sources": {
            "code_claude_com": CLAUDE_CODE_BASE_URL,
            "platform_claude_com": PLATFORM_BASE_URL
        },
        "total_files": len(fetched_files),
        "fetch_tool_version": "2.0.0"
    }

    # Save new manifest
    save_manifest(docs_dir, new_manifest)

    # Summary
    duration = datetime.now() - start_time
    logger.info("\n" + "="*50)
    logger.info(f"Fetch completed in {duration}")
    logger.info(f"Discovered pages: {total_discovered}")
    logger.info(f"Successful: {successful}/{total_discovered}")
    logger.info(f"Failed: {failed}")
    
    if failed_pages:
        logger.warning("\nFailed pages (will retry next run):")
        for page in failed_pages:
            logger.warning(f"  - {page}")
        # Don't exit with error - partial success is OK
        if successful == 0:
            logger.error("No pages were fetched successfully!")
            sys.exit(1)
    else:
        logger.info("\nAll pages fetched successfully!")


if __name__ == "__main__":
    main()