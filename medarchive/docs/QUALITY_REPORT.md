# Quality Report

## Status

No quality metrics have been generated yet.

## Planned Checks

- Input file coverage.
- Parsing completeness.
- Field validation failures.
- Matching precision and review outcomes.
- Unmatched or ambiguous records.
- Anomaly flag counts by code and severity.
- Verification action status counts.
- Active versus inactive price item version counts.
- Duplicate and >50% price-change review queues.

## Implemented Inputs

- `anomaly_flags` stores validation and history anomalies.
- `verification_actions` stores follow-up actions opened from anomaly flags.
- `price_item_versions` stores active/inactive history rows and supersede chains.

## Reporting Policy

Quality reports should clearly separate synthetic demo results from any future approved real-data evaluation.
