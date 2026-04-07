# n8n Workflow Notes

This project is designed so n8n can trigger one run, then consume `data/insights/latest_insight.json`.

Recommended flow:

1. `Schedule Trigger` node.
2. `Execute Command` node:

```bash
cd /workspace/doomscroll-agent
python3 -m src.run_pipeline --once
```

3. `Read Binary File` or `Read/Write Files from Disk` node:
   - Path: `/workspace/doomscroll-agent/data/insights/latest_insight.json`
4. Optional downstream nodes:
   - Slack
   - Email
   - Google Sheets
   - Webhook

Operational notes:

- Keep environment variables in the n8n container or host environment rather than hardcoding them in the workflow.
- Use `TARGET_PLATFORM=reddit` for the current stable path.
- TikTok support is scaffolded, but not yet the reliable demo path.
