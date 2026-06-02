# integrations/n8n

Automate [YakYak](https://yakyak.ai/) visually with **[n8n](https://n8n.io/)**.

This integration provides n8n nodes and ready-made workflow templates that call the
[YakYak API](https://api.yakyak.ai/api/docs), so you can build no-code/low-code
automations around the media pipeline — for example, generate and publish a new
episode on a schedule, or trigger a render from an external event.

## What's here

- **Credentials** definition for the YakYak Bearer-JWT auth.
- **Nodes** wrapping the **Workflow**, **Scheduler**, **Social**, and **Data**
  endpoints.
- **Workflow templates** (`.json`) you can import into n8n — e.g. *create campaign
  → generate episode → render → post to socials*.

## Reference

- **API docs:** https://api.yakyak.ai/api/docs
- **OpenAPI spec:** https://api.yakyak.ai/api/docs-json

## Usage

Import a template from this folder into your n8n instance, set the YakYak
credential, and run or schedule the workflow.
