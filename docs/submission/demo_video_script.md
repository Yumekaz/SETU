# SETU — 3–4 minute recording script

Use the running Docker application at `http://127.0.0.1:5173`. Record at 1920×1080 where possible, keep the browser at 1280px width or above, and keep system audio off.

## Before recording

1. Start the stack: `docker compose up -d --build`.
2. Open `http://127.0.0.1:5173` and wait for **Overview** to load.
3. Open **Scenario replay** once before recording and locate the 2026-02-10 crossing.
4. Return to **Overview** and leave the incident analysis unrun, so the recording shows its full state transition.
5. Use a calm, direct voice. Pause after each meaningful result; do not narrate every label.

## Script

| Time | Screen action | Say this |
|---|---|---|
| 0:00–0:25 | Switch to **Scenario replay**, paused on 2026-02-10. | "India’s crude supply is exposed to a small number of maritime corridors. SETU turns geopolitical evidence into an operational decision. In this historical Hormuz replay, SETU first crossed its risk threshold on 10 February 2026—20 days before the publicly reported 2 March closure of the Strait of Hormuz." |
| 0:25–0:50 | Show the replay headline, score, and timeline. | "This is a reproducible result, not a retrospective threshold fit. The threshold was locked at 0.437501 from a separate 17-day January baseline. We are precise about the boundary: this is one historical case, not a claim of broad detection accuracy." |
| 0:50–1:10 | Switch to **Overview** and show the risk and forecast panels. | "Once a signal is detected, SETU makes the decision chain visible: source evidence, structured corridor risk, forecast uncertainty, network impact, and mitigation choices." |
| 1:10–1:55 | Click **Run incident analysis**. Let the five stages complete. | "I’ll now run the operational workflow. SETU ingests a reference incident source, extracts a Hormuz military event, updates the risk state, runs a forecast, simulates the downstream cascade, and generates feasible mitigation options." |
| 1:55–2:25 | Point to the verified source evidence and completed stages. | "The source, publisher, evidence terms, timestamps, and confidence are shown with the result. That traceability is important: the decision is tied to inspectable evidence, not an unexplained alert." |
| 2:25–2:55 | Show cascade and recommendation panels. | "The cascade translates corridor disruption into supply and price ranges. The recommendations make the trade-offs explicit—risk reduction, time penalty, and strategic-reserve use—while the final approval stays with a human operator." |
| 2:55–3:15 | Switch to **Maritime network** and change the corridor focus. | "The maritime view connects the signal to the physical trade network and compares the relevant route response. These route waypoints are reference geometry, not a claim of live AIS vessel tracking." |
| 3:15–3:40 | Return to **Scenario replay** or show the repository URL. | "SETU is built as a transparent decision-support system: constrained extraction, deterministic scoring and optimization, and documented limitations. The historical result is N=1 with a short baseline; the product and reproducibility details are available in this repository." |

## Common technical questions

**"How confident are you in the 20-day result?"**

"It is a reproducible N=1 historical result. The 0.437501 threshold was derived from a separate 17-day January baseline and locked before the February–March evaluation. That is encouraging evidence, not broad statistical validation; we document that limitation directly."

**"Why did February 28 not cross but March 2 did?"**

"This replay requires source-deduplicated, same-day direct Hormuz evidence. February 28 did not have enough direct corridor evidence to meet the pre-locked threshold. By March 2, corroborated closure reporting did. Earlier signals remain context, but they cannot substitute for direct evidence in this metric."

**"Is this all live data?"**

"The product supports article ingestion and a GDELT refresh. This recording uses a stable reference incident and a committed historical cache so the result can be reproduced. We show the source and clearly distinguish evidence from static reference geometry."

**"Why should a team trust the recommendations?"**

"They should not blindly trust them. SETU exposes the evidence, uncertainty, and trade-offs, and leaves the final approval to a human operator."

**"What is not in the MVP?"**

"AIS vessel tracking, refined-product modeling, multilingual sources, and broader multi-event validation are explicitly documented as next steps, not presented as finished capabilities."

## Recording checklist

- Show the 2026-02-10 crossing before operational workflow.
- State the 20-day result and N=1 / 17-day-baseline boundary verbatim.
- Show source URL, evidence terms, and confidence.
- Show all five incident-analysis stages complete and one recommendation’s trade-offs.
- Keep the recording between 3 and 4 minutes; end with the GitHub repository URL on screen or in the description.
