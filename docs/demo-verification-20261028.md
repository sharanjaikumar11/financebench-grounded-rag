# Demo verification — 28 October 2026

Checked the actual `streamlit_app.py` with Streamlit AppTest and local HTTP access.

| Check | Result |
| --- | --- |
| App startup and title rendering | Passed; no AppTest exceptions |
| Chat submission without Gemini key | Passed; clear key-required UI error |
| Saved answer and citation rendering | Passed using an actual latest-run answer |
| PDF source link | Passed; URL contains the cited page fragment |
| PDF HTTP delivery | Passed; HTTP 200, application/pdf and PDF signature |
| Unit suite | 290 passed |

Sandbox-local sockets were blocked, so app/HTTP checks were repeated outside that
sandbox successfully. No application changes were necessary for these checks.
The saved-answer check is a rendering test, not a fresh RAG answer. No Gemini key
is available in this process, so a fresh model request through Streamlit was not
tested. Browser PDF-viewer scrolling to the fragment was not visually verified.
Fresh-machine installation, Docker and production deployment were not tested.

Use the current validation environment block in README and a keyed PowerShell
terminal to launch the demo. A successful 50-case collector run does not by itself
verify the demo's complete live path: the demo uses K=3 and the collector K=5.
