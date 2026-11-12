---
name: douyin-web-api
description: Inspect and maintain a documented catalog of Douyin website requests and official OpenAPI routes. Use when mapping Douyin web features or checking an endpoint; use the separate download skill for video downloads.
---

# Douyin web API catalog

Read [references/api-catalog.md](references/api-catalog.md) for observed website routes, first-party script findings, and official OpenAPI references. Use [references/observed-routes.json](references/observed-routes.json) when the exact observed parameter names or status codes matter. Check the evidence label on each route: an observed GET with a successful response does not prove a related write route works. The website's internal endpoints and the OAuth-based OpenAPI use different credentials and may change independently.

When the user asks for a fresh capture, visit only the requested pages with an authorized browser session. Record host, method, path, parameter names, HTTP status, business status and the page action that triggered the request. Keep request headers, Cookie values, signed query values, user identifiers, response bodies and raw HAR files out of shared documentation. A reusable capture helper is in [scripts/capture_routes.py](scripts/capture_routes.py). Install [requirements.txt](requirements.txt) and Playwright Chromium, then run `python scripts/capture_routes.py --cookies <local-cookie-json>`. Its output goes to the ignored `data/capture/` directory by default. The helper navigates pages without clicking account action buttons; the site may automatically emit POST telemetry or history requests.

For an action the user intends to take, verify the current first-party route and required authorization separately. A catalog entry is reference material, not proof that a request can be replayed. Use the official OpenAPI where its granted OAuth permissions fit the task; a browser Cookie does not substitute for OAuth access tokens.
