# SETU - 3 to 4 minute product walkthrough script

Use the running Docker dashboard at `http://127.0.0.1:5173`. Keep the browser at 1280px width or above, record at 1080p, and use the **Run Incident Response Workflow** button once during the video.

## Before recording

1. Start the stack: `docker compose up -d --build`
2. Open `http://127.0.0.1:5173` and wait for the dashboard to load.
3. Ensure the top explainer card and **Incident Workflow** panel are visible.
4. Do not pre-run the workflow in the recording tab. The completed steps illustrate the operational sequence.
5. Use a calm voice. Show the screen; do not read every number.

## Script

| Time | Screen action | Say this |
|---|---|---|
| 0:00-0:20 | Show the top of the dashboard. | "India's crude supply is vulnerable to disruptions in a few maritime corridors. During a crisis, teams do not need another news feed - they need a defensible response quickly. SETU is an AI-powered decision-support system for that problem." |
| 0:20-0:42 | Point to the explainer and credibility table. | "SETU turns a geopolitical signal into a decision trail. It ingests evidence, identifies the affected crude corridor, forecasts risk, simulates the downstream impact, and recommends mitigation. We deliberately make the source, confidence, timestamps, and evidence terms visible so a user can inspect the basis of the decision." |
| 0:42-0:55 | Scroll to the Incident Workflow panel. | "Rather than showing disconnected features, this control runs the complete source-to-decision workflow using a reference incident source. I will now run it end to end." |
| 0:55-1:50 | Click **Run Incident Response Workflow**. Pause while the five steps complete. | "First, SETU ingests the source and extracts a HORMUZ military disruption event. You can see the AP article title, publisher, source URL, timestamps, matched terms, and confidence. This is important: the event is not just a hard-coded dashboard row; it is evidence that updates the corridor risk." |
| 1:50-2:20 | Point to completed forecast and cascade stages, then the map/cascade area. | "Next, the system runs a short-horizon risk forecast from the updated state, then propagates the disruption through the crude supply network using a Monte Carlo cascade simulation. The result is an operational impact view rather than a generic alert." |
| 2:20-2:55 | Scroll to the recommendation panel. | "SETU then generates mitigation options. Each option explains why it is recommended and makes the trade-off visible: risk reduction, time penalty, and cost impact. The final decision remains human-in-the-loop - an operator can approve or reject the recommendation with an audit trail." |
| 2:55-3:20 | Show the evidence/recommendation panels together if possible. | "The innovation is the full chain from credible source evidence to an explainable operational action. The UI de-emphasizes weak seeded rows so they are not confused with evidence, and the one-click flow makes the decision path easy to inspect." |
| 3:20-3:45 | Return to the explainer card or final dashboard view. | "This is a working MVP built with React, FastAPI, SQLite, typed JSON contracts, deterministic scoring and orchestration, and a containerized local deployment path. Its next step is integrating validated AIS, supplier, refinery, and market data feeds for production deployment. SETU turns a geopolitical signal into an explainable energy-supply decision." |

## Common technical questions

**"Is this all live data?"**

"The guided workflow uses a credible reference news source for a stable, reproducible operational walkthrough. SETU also supports source URL ingestion and a live GDELT trigger. External data availability varies, so we show the source and clearly distinguish evidence from seeded data."

**"What is the AI part?"**

"The intelligence layer converts geopolitical text into structured event signals. We intentionally keep scoring, simulation, and recommendation logic deterministic and inspectable, because operational decisions require repeatability and explanation."

**"Why should a team trust the recommendations?"**

"They should not blindly trust them. SETU exposes the evidence, uncertainty, and trade-offs, and leaves the final approval to a human operator."

**"What is not in the MVP?"**

"AIS vessel tracking, refined-product modeling, multilingual sources, and broader multi-event validation are explicitly documented as next steps, not presented as finished capabilities."

## Recording checklist

- Show source URL, evidence terms, and confidence.
- Show all five Incident Workflow stages complete.
- Show at least one recommendation's explanation and human approval gate.
- Keep the video between 3 and 4 minutes.
- End with the GitHub repository URL on screen or in the video description.
