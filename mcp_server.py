"""ATS Zero-Browser Gateway - MCP server (thin client).

Exposes the hosted Apify Actor ``ginugokz/ats-zero-browser-gateway`` as MCP tools
for Claude, Cursor, n8n agents and any MCP client.

The extraction engine runs on Apify. This client only forwards tool calls to the
Actor's API and returns the dataset items, so it has no scraping dependencies.

Authentication: set ``APIFY_TOKEN`` (https://console.apify.com/settings/integrations).
The server starts and lists its tools without a token; a token is needed only when a
tool is called. Runs are billed pay-per-event on Apify (see the Actor's Pricing tab).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

try:  # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer as _Server
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # MCP Python SDK 1.x
    from mcp.server.fastmcp import FastMCP as _Server
    from mcp.server.fastmcp.exceptions import ToolError

ACTOR_ID = "ginugokz~ats-zero-browser-gateway"
RUN_SYNC_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
STORE_URL = "https://apify.com/ginugokz/ats-zero-browser-gateway"
# run-sync waits up to 300 s for the run; keep the HTTP timeout above that so a
# slow run is never abandoned (and silently re-run) by the client.
HTTP_TIMEOUT_S = 320
MAX_TARGETS = 200

server = _Server("ats-zero-browser-gateway")


def _token() -> str:
    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not token:
        raise ToolError(
            "APIFY_TOKEN is not set. Copy your API token from "
            "https://console.apify.com/settings/integrations and set it as the "
            f"APIFY_TOKEN environment variable. Actor: {STORE_URL}"
        )
    return token


def _run_actor(actor_input: dict[str, Any]) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        RUN_SYNC_URL,
        data=json.dumps(actor_input).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_token()}",
            "User-Agent": "ats-zero-browser-gateway-mcp/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
            raw = response.read().decode("utf-8") or "[]"
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise ToolError(f"Apify API returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ToolError(f"Could not reach the Apify API: {exc.reason}") from exc
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ToolError(f"Unexpected response from Apify: {str(payload)[:300]}")
    return payload


@server.tool()
def scrape_ats_jobs(
    urls: list[str],
    only_deltas: bool = False,
    max_jobs: int = 40,
    include_details: bool = True,
) -> dict[str, Any]:
    """Extract open job postings from Workday, Greenhouse, Lever and Ashby career sites.

    Args:
        urls: Full career-site URLs; the ATS is detected from the host
            (myworkdayjobs.com, myworkdaysite.com, greenhouse.io, lever.co,
            ashbyhq.com). Bare board names such as "stripe" are rejected. Examples:
            "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite",
            "https://boards.greenhouse.io/stripe", "https://jobs.lever.co/spotify",
            "https://jobs.ashbyhq.com/ramp".
        only_deltas: Return only jobs that are ADDED, UPDATED or REMOVED since the
            previous run (change tracking is stored in your Apify account).
        max_jobs: Maximum jobs per company, 1-500.
        include_details: Include full job descriptions and salary extraction.

    Returns a dict with ``count`` and ``jobs`` (title, url, locations, posted_date,
    employment_type, remote_type, compensation_raw, description_html, delta_status,
    source_system: workday_cxs | greenhouse | lever | ashby, ...).
    Billing: pay-per-event on Apify; see the Actor's Pricing tab.
    """
    targets = [u.strip() for u in urls if isinstance(u, str) and u.strip()]
    if not targets:
        raise ToolError("Provide at least one career-site URL or board token.")
    if len(targets) > MAX_TARGETS:
        raise ToolError(f"At most {MAX_TARGETS} career sites per call.")
    items = _run_actor(
        {
            "targets": targets,
            "only_deltas": bool(only_deltas),
            "max_jobs": max(1, min(int(max_jobs), 500)),
            "include_details": bool(include_details),
        }
    )
    return {"count": len(items), "jobs": items}


if __name__ == "__main__":
    server.run()  # stdio transport
