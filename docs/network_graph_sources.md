# Network Graph Data Sources — Phase 2

Authoritative graph: [`data/graph/india_crude_network.json`](../data/graph/india_crude_network.json)

## Cited sources

| Source | URL | Use in SETU |
|---|---|---|
| EIA Open Data | https://www.eia.gov/opendata/ | India crude import volume context (`eia_india_imports_sample.json`) |
| PPAC India | https://www.ppac.gov.in/ | Public petroleum import dependency statistics |
| Hormuz 2026 timeline | [`data/hormuz_2026_timeline.csv`](../data/hormuz_2026_timeline.csv) | Duration distribution + Brent directional anchor |

## ASSUMPTION (documented, VERIFY on portal)

- Total India seaborne crude imports scaled to **~5.0 mbpd**
- Corridor share of inflow: **Hormuz ~60%**, **Malacca ~24%**, **Bab-el-Mandeb ~16%**
- Node capacities and edge `flow_mbpd` values are proportional allocations from these shares

## Topology

```
PRODUCTION_FIELD → CORRIDOR → PORT → REFINERY → DEMAND_CENTER
```

Semantic node IDs (`corridor_hormuz`, `port_mumbai`, `refinery_jamnagar`, `demand_north`) replace the Phase 0 random `node_1` chain.