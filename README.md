# 3PL KPI Tracker Agent

An agentic scorecard project for transportation teams that compare third-party logistics providers. It ingests shipment records, calculates provider KPIs, tests them against configurable targets, and produces prioritized management alerts.

## Agents

| Agent | Responsibility |
| --- | --- |
| Data Quality Agent | Validates required fields, numeric values, dates, and status codes. |
| KPI Agent | Calculates on-time delivery, order accuracy, damage-free delivery, exception rate, transit time, and cost per shipment. |
| Performance Alert Agent | Compares each provider with targets and ranks failed KPIs. |
| Coordinator | Returns provider scorecards, alerts, and an interaction trace. |

## KPIs

- On-time delivery rate
- Order accuracy rate
- Damage-free delivery rate
- Exception rate
- Average transit days
- Average cost per shipment

## Run

```bash
python -m src.kpi_tracker --shipments data/shipments.csv --targets targets.json
python -m unittest discover -s tests -v
```

## Data contract

Each CSV row represents one shipment. Boolean fields use `1` for yes and `0` for no. The included rows use unmistakably fictitious ExampleCarrier names and synthetic values.

## Production extensions

- Connect the ingestion agent to a TMS, WMS, EDI feed, or warehouse database.
- Add volume weighting, service-level segmentation, lane benchmarking, and rolling trends.
- Display scorecards in Streamlit, Power BI, Tableau, or an internal web application.
- Route high-severity alerts to vendor-management workflows.
- Add an LLM narrative agent that explains KPI changes while preserving the underlying calculations.

## License

MIT
