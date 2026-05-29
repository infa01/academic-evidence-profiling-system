# Developer Tools

These scripts are inspection/debugging helpers. They are not part of the
canonical thesis pipeline and should not be treated as methodology steps.

## Scripts

- `analyze_results.py` summarises extracted LO-to-ESCO evidence from the latest
  filtered output.
- `inspect_esco_dataset.py` inspects the local ESCO classification archive.
- `inspect_esco_jsonld.py` creates a local inspection report for ESCO JSON-LD
  structure.
- `evaluate_cross_encoder_reranking.py` runs a diagnostic cross-encoder
  re-ranking audit over existing ESCO candidates. It does not modify the
  canonical pipeline.

Run them manually only when checking data quality or debugging setup:

```powershell
python scripts\dev_tools\analyze_results.py
python scripts\dev_tools\inspect_esco_dataset.py
python scripts\dev_tools\inspect_esco_jsonld.py
python scripts\dev_tools\evaluate_cross_encoder_reranking.py
```
