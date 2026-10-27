# Lakehouse Table Health report

A Power BI project (PBIP) that shows the output of [`sys.sp_get_table_health_metrics`](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-get-table-health-metrics-transact-sql?view=fabric) for every table in one or more Fabric lakehouses. Blog post: [A Health Dashboard for Your Fabric Lakehouse Tables](https://glorious-manta.pages.dev/posts/lakehouse-table-health-dashboard/).

The report reads a Direct Lake semantic model on a single Delta table, `table_health_snapshots`. You fill that table yourself: loop over the tables of a lakehouse, call the procedure once per table and append the results with a snapshot timestamp.

## Expected table

`table_health_snapshots` in the lakehouse the model points to, one row per table per scan:

| Column | Type | Content |
|---|---|---|
| `snapshot_ts` | timestamp | Time of the scan |
| `workspace` | string | Workspace of the scanned lakehouse |
| `lakehouse` | string | Name of the scanned lakehouse |
| `table` | string | `schema.table` |
| `status` | string | `healthy`, `unhealthy` or `unknown` (the procedure call failed) |
| `error` | string | Error message when the call failed, else null |
| `PotentialAnomalyType` | int | From the procedure |
| `PotentialAnomalyDescription` | string | From the procedure |
| `SnapshotVersion`, `CheckpointVersion` | int | From the procedure |
| `PhysicalRowCount`, `DeletedRowCount` | int | From the procedure |
| `FileCount`, `DeleteBitmapCount`, `FileSizeInBytes` | int | From the procedure |

Extra columns, such as the histograms, are ignored by the model.

## Setup

1. Open `LakehouseTableHealth.SemanticModel/definition/expressions.tmdl` and replace `<workspace-id>` and `<lakehouse-id>` with the IDs of the lakehouse that holds `table_health_snapshots`. You find both in the lakehouse URL.
2. Open `LakehouseTableHealth.pbip` in Power BI Desktop.
3. Allow the [HTML Content](https://html-content.com/) custom visual if your tenant asks for it.
4. Refresh the model and publish.

## How the report behaves

- Workspace, Lakehouse and Health status slicers filter every visual.
- KPIs count tables by workspace + lakehouse + table name.
- The KPIs use the latest snapshot for the selected workspace and lakehouse. With several lakehouses selected, the report uses the most recent timestamp across the selection, so lakehouses you scan separately can need their own selection.
- The trend shows scans from the 30 days before the latest snapshot.
- Maintenance priorities lists scan errors first, then invalid statistics, then other anomalies by file count. It shows up to 100 rows. The suggested actions follow the procedure's documented anomaly codes and don't run anything.
- The HTML visuals are display-only: no cross-filtering, column sorting or export.

## Validation

`python3 tools/validate_report.py` runs static checks on the JSON, visual layout, measure bindings and DAX string delimiters. It doesn't execute DAX or render the report.
