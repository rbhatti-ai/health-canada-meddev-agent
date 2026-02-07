#!/usr/bin/env python3
"""
Project State Snapshot Generator

Generates a Markdown report of current project state including:
- Git status (branch, last commit, dirty files)
- Database state (tables, RLS, policies)
- Test results summary
- File counts and structure
- Known gaps vs architecture

Output: docs/PROJECT_STATE_SNAPSHOT.md

Usage:
    python scripts/snapshot.py
    make snapshot
"""


# Edmonton timezone (Mountain Time)
import os
import subprocess
from pathlib import Path

os.environ["TZ"] = "America/Edmonton"

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = REPO_ROOT / "docs" / "PROJECT_STATE_SNAPSHOT.md"

DB_USER = "meddev"
DB_NAME = "meddev_agent"


def run_cmd(cmd: str, timeout: int = 10) -> str:
    """Run a shell command and return stdout. Return error string on failure."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(REPO_ROOT),
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"


def psql(query: str) -> str:
    """Run a psql query against local dev DB."""
    return run_cmd(f'psql -U {DB_USER} -d {DB_NAME} -t -A -c "{query}"')


def get_timestamp() -> str:
    """Get current timestamp in Mountain Time."""
    return run_cmd("TZ='America/Edmonton' date '+%Y-%m-%d %H:%M:%S MST'")


def get_git_info() -> dict:
    """Get git branch, last commit, and status."""
    return {
        "branch": run_cmd("git branch --show-current"),
        "last_commit": run_cmd("git log -1 --oneline"),
        "commit_hash": run_cmd("git rev-parse --short HEAD"),
        "dirty_files": run_cmd("git status --porcelain"),
        "total_commits": run_cmd("git rev-list --count HEAD"),
    }


def get_db_tables() -> str:
    """Get list of tables in public schema."""
    return psql("SELECT tablename FROM pg_tables " "WHERE schemaname='public' ORDER BY tablename;")


def get_rls_state() -> str:
    """Get RLS state for all public tables."""
    return psql(
        "SELECT tablename || '|' || rowsecurity FROM pg_tables "
        "WHERE schemaname='public' ORDER BY tablename;"
    )


def get_policies() -> str:
    """Get all RLS policies."""
    return psql(
        "SELECT tablename || '|' || policyname || '|' || cmd "
        "FROM pg_policies WHERE schemaname='public' ORDER BY tablename;"
    )


def get_test_summary() -> str:
    """Run pytest in collection mode to count tests."""
    return run_cmd(
        "source venv/bin/activate && python -m pytest --co -q 2>&1 | tail -1",
        timeout=30,
    )


def count_files() -> dict:
    """Count source files by type."""
    py_src = run_cmd("find src -name '*.py' -not -path '*__pycache__*' | wc -l")
    py_test = run_cmd("find tests -name '*.py' -not -path '*__pycache__*' | wc -l")
    sql = run_cmd("find scripts -name '*.sql' | wc -l")
    return {
        "python_src": py_src.strip(),
        "python_test": py_test.strip(),
        "sql_migrations": sql.strip(),
    }


def generate_snapshot() -> str:
    """Generate the full snapshot markdown."""
    ts = get_timestamp()
    git = get_git_info()
    tables = get_db_tables()
    rls = get_rls_state()
    policies = get_policies()
    test_summary = get_test_summary()
    files = count_files()

    # Format RLS table
    rls_rows = ""
    for line in rls.split("\n"):
        if "|" in line:
            table, enabled = line.split("|")
            status = "ON" if enabled == "t" else "OFF"
            rls_rows += f"| {table} | {status} |\n"

    # Format policies table
    policy_rows = ""
    if policies and policies != "":
        for line in policies.split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    policy_rows += f"| {parts[0]} | {parts[1]} | {parts[2]} |\n"
    else:
        policy_rows = "| (none) | (none) | (none) |\n"

    # Format dirty files
    dirty = ""
    if git["dirty_files"]:
        for line in git["dirty_files"].split("\n"):
            if line.strip():
                dirty += f"  - `{line.strip()}`\n"
    else:
        dirty = "  - Clean working directory\n"

    md = f"""# PROJECT STATE SNAPSHOT

> **Generated:** {ts}
> **Generator:** `scripts/snapshot.py`
> **This file is auto-generated. Do not edit manually.**

---

## Git Status

| Field | Value |
|-------|-------|
| Branch | `{git['branch']}` |
| Last Commit | `{git['last_commit']}` |
| Commit Hash | `{git['commit_hash']}` |
| Total Commits | {git['total_commits']} |

**Uncommitted changes:**
{dirty}
---

## Test Summary
```
{test_summary}
```

---

## File Counts

| Category | Count |
|----------|-------|
| Python source files (src/) | {files['python_src']} |
| Python test files (tests/) | {files['python_test']} |
| SQL migration files | {files['sql_migrations']} |

---

## Database State (Local Postgres)

### Tables
```
{tables}
```

### Row-Level Security

| Table | RLS |
|-------|-----|
{rls_rows}
### Policies

| Table | Policy | Command |
|-------|--------|---------|
{policy_rows}
---

## Known Gaps vs Governing Architecture

| Requirement | Status | Notes |
|-------------|--------|-------|
| Regulatory Twin (persistent) | PARTIAL | DeviceInfo model exists, no persistent storage |
| Traceability Engine | NOT STARTED | trace_links table exists, no UI/logic |
| Evidence Gap Detection | NOT STARTED | No rules engine |
| Submission Readiness Dashboard | NOT STARTED | No dashboard UI |
| Document Orchestration | NOT STARTED | No doc generation from structured data |
| Deficiency Response Workflow | NOT STARTED | No deficiency tracking |
| AI Provenance (ai_runs) | PARTIAL | Table + logger exist, no UI/approval flow |
| Human-in-the-Loop Approval | NOT STARTED | No approval workflow |
| RLS / Multi-Tenancy | IN PROGRESS | RLS enabled, policies Supabase-only |
| S3 Document Storage | NOT STARTED | No S3 integration |
| Supabase Cloud Deployment | NOT STARTED | Local Postgres only |

---

## Checkpoint History

| Timestamp | Commit | Description |
|-----------|--------|-------------|
| {ts} | `{git['commit_hash']}` | Auto-snapshot |

---

*End of snapshot*
"""
    return md


def main() -> None:
    """Generate and write snapshot."""
    print("Generating project snapshot...")
    md = generate_snapshot()
    OUTPUT_FILE.write_text(md)
    print(f"Snapshot written to: {OUTPUT_FILE}")
    print(f"Timestamp: {get_timestamp()}")


if __name__ == "__main__":
    main()
