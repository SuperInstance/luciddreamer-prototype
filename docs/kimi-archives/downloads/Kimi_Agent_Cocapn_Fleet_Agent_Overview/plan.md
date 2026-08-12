# Cocapn Fleet Agent — Health Audit Plan

## Objective
Run a full health audit of the Cocapn fleet, identify why 6 services are DOWN, and deliver a diagnostic report with fix recommendations.

## Stage 1 — Discovery & Baseline
- Clone `cocapn-health` repository
- Read README and understand how the health checker works
- Run `python -m cocapn_health --host 147.224.38.131 --ports all` to get baseline

## Stage 2 — LIVE Service Validation
- Manually curl each of the 6 LIVE endpoints to confirm they respond
- Document response payloads

## Stage 3 — DOWN Service Diagnosis
- For each of the 6 DOWN services, curl the endpoint
- Classify failure mode: connection refused, timeout, HTTP error, malformed response
- Cross-check ports against any source code or configs found in repos

## Stage 4 — Analysis & Recommendations
- Summarize findings per service
- Propose root causes and fix steps
- Generate the final report

## Report Format
Per mission rules: Agent / Task / Status / What I Did / What I Found / Deliverables / Next Step
