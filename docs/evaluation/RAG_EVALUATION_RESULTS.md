# RAG Evaluation Results

This document records the final lightweight RAGAS-inspired proxy evaluation
results used for dissertation defence. These metrics are diagnostic checks, not
official RAGAS/ARES output and not expert validation.

## Generic and Targeted Runs

| Run | Context precision | Section relevance | Faithfulness | Answer relevance | Evidence mention coverage | Quality gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Baseline generic | 0.94 | 0.55 | 1.00 | 0.73 | 1.00 | Passed |
| Advisor case 01 generic | 0.94 | 0.56 | 0.72 | 0.63 | 0.78 | Passed |
| Advisor case 02 generic | 1.00 | 0.54 | 0.95 | 0.69 | 0.94 | Passed |
| Advisor case 03 generic | 0.94 | 0.51 | 0.78 | 0.63 | 0.94 | Passed |
| Targeted database administrator | 0.90 | 0.67 | 0.95 | 0.75 | 0.85 | Passed |

## Interpretation

The results show consistently high context precision across the generated
reports, which indicates that retrieved chunks were usually above the configured
relevance threshold. Faithfulness was also high in the baseline and targeted
runs, although two advisor cases were lower, showing that the metric is useful as
a diagnostic check rather than a proof of correctness.

Section relevance is the weakest metric, especially for the generic advisor
cases. This does not automatically mean that the reports are unusable; it means
that the generated section text is not always semantically close to the section's
retrieved chunk bundle according to the embedding proxy. This should be reported
as a limitation of the automated evaluation method and as evidence that human or
expert review remains necessary.

The targeted database administrator report passed the deterministic quality gate
after prompt refinement. The final run included all six required sections, no
forbidden overclaiming phrases, and stored retrieved evidence, prompt and
metadata for audit.

