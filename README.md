# Workday, Greenhouse, Lever & Ashby Jobs API — MCP server + Apify Actor

Get every open job from company career sites running **Workday**, **Greenhouse**, **Lever** or **Ashby** as clean, normalized JSON — with **change tracking**: only the jobs that were added, updated or closed since your last run. No browser, no login, no proxies.

This repository contains the **MCP server** and **integration templates**. The extraction engine runs as a hosted, maintained Actor on Apify:

**→ [ginugokz/ats-zero-browser-gateway on Apify](https://apify.com/ginugokz/ats-zero-browser-gateway)**

---

## What you get

- **One schema for 4 applicant tracking systems** — Workday (`myworkdayjobs.com`, `myworkdaysite.com`), Greenhouse, Lever and Ashby.
- **Change tracking (`only_deltas`)** — receive only `ADDED`, `UPDATED` and `REMOVED` jobs since the previous run. Built for daily monitoring in n8n, Make, Zapier, Clay or your own pipeline.
- **Salary text** extracted when the posting publishes it (`compensation_raw`).
- **Privacy by default** — recruiter emails and phone numbers are removed from descriptions.
- **Fast** — around 40 detailed Workday jobs in about 10 seconds, with no headless browser.

## Supported career sites

| ATS | Example input |
|---|---|
| Workday | `https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite` |
| Greenhouse | `https://boards.greenhouse.io/stripe` or `stripe` |
| Lever | `https://jobs.lever.co/spotify` or `spotify` |
| Ashby | `https://jobs.ashbyhq.com/ramp` or `ramp` |

## Quick start

### 1. No code

Open the [Actor on Apify](https://apify.com/ginugokz/ats-zero-browser-gateway), paste one or more career-site URLs and click **Start**. Export the results as JSON, CSV or Excel, or schedule the Actor to run daily.

### 2. HTTP API (any language)

```bash
curl -X POST "https://api.apify.com/v2/acts/ginugokz~ats-zero-browser-gateway/run-sync-get-dataset-items" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
        "targets": ["https://boards.greenhouse.io/stripe", "https://jobs.ashbyhq.com/ramp"],
        "only_deltas": true,
        "max_jobs": 100
      }'
```

Get your API token at [console.apify.com/settings/integrations](https://console.apify.com/settings/integrations).

### 3. Python

```python
import os, requests

resp = requests.post(
    "https://api.apify.com/v2/acts/ginugokz~ats-zero-browser-gateway/run-sync-get-dataset-items",
    headers={"Authorization": f"Bearer {os.environ['APIFY_TOKEN']}"},
    json={"targets": ["https://jobs.lever.co/spotify"], "only_deltas": True},
    timeout=320,
)
for job in resp.json():
    print(job["delta_status"], job["title"], job["url"])
```

### 4. MCP — Claude Desktop, Cursor and other MCP clients

**Hosted (nothing to install):** add the Apify MCP server with this Actor as a tool:

```
https://mcp.apify.com/?tools=ginugokz/ats-zero-browser-gateway
```

**Local (this repository):**

```bash
pip install "mcp>=1.2"
```

```json
{
  "mcpServers": {
    "ats-jobs": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server.py"],
      "env": { "APIFY_TOKEN": "<your Apify API token>" }
    }
  }
}
```

Tool exposed: `scrape_ats_jobs(urls, only_deltas=False, max_jobs=40, include_details=True)`.
The server starts without a token; the token is only needed when the tool is called.

### 5. n8n

Import [`templates/n8n_ats_delta_monitor.json`](templates/n8n_ats_delta_monitor.json): it runs every 12 hours, calls the Actor with `only_deltas` and `full_scan`, and routes new, closed and edited jobs to three outputs (connect them to Slack, email or Sheets). Authentication: create a **Header Auth** credential with Name `Authorization` and Value `Bearer <your Apify API token>`, then select it in the HTTP Request node.

## Output

One item per job. Example:

```json
{
  "source_system": "workday",
  "company_tenant": "nvidia",
  "requisition_id": "JR1987654",
  "title": "Senior Deep Learning Architect",
  "url": "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/JR1987654",
  "locations": ["Santa Clara, CA", "Remote - US"],
  "posted_date": "2026-10-14",
  "employment_type": "Full time",
  "remote_type": "Hybrid",
  "compensation_raw": "$220,000 - $340,000 USD Annual",
  "delta_status": "ADDED",
  "scraped_at": "2026-10-15T19:47:48Z"
}
```

## How change tracking works

| `delta_status` | Meaning |
|---|---|
| `ADDED` | New job since the previous run |
| `UPDATED` | Title, description or compensation changed |
| `REMOVED` | Job no longer listed (reported only after a complete, consistent read; a sudden drop to zero jobs waits for a second run) |
| `EXISTING` | Unchanged — skipped when `only_deltas` is `true` |

The tracking state is stored in a named key-value store in **your own** Apify account. To track closed jobs on large career sites, set `full_scan: true` (summary mode, up to 5,000 jobs per site); a partial read never reports `REMOVED`.

## Pricing

Pay-per-event on Apify: you pay per job delivered plus a small fee per run. Current prices are on the Actor's **Pricing** tab. Apify's free plan includes monthly usage credit for testing.

## FAQ

**Is this legal?** The Actor reads the same public job-board endpoints that companies' own career pages use to show their openings. No login is used. It returns job postings, not personal profiles, and strips recruiter emails and phone numbers.

**Why isn't the extraction engine in this repository?** It runs as a managed service on Apify so that fixes for changing ATS endpoints reach every user immediately. This repository is the client side: MCP server, API examples and workflow templates.

**Can I monitor hundreds of companies?** Yes — pass them all in `targets` in one run and schedule it daily with `only_deltas: true`.

## License

MIT — applies to the code in this repository (MCP client and templates).
