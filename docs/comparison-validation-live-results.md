# Comparison validation: first live result

Candidate: `evaluation/results/generation_50_comparison_validation.json`.
Baseline: `evaluation/results/generation_50_calculation_render_v2.json`.
Both have 50 completed cases and no provider-error cases. The candidate records
comparison, calculation and repair-excerpt flags enabled; configured model and
thinking settings match the baseline. Other prompt changes also occurred between
runs, so this is not an isolated causal measurement of comparison validation.

| Measure | Baseline | Candidate |
|---|---:|---:|
| Strict citation-location matches | 30/50 (60%) | 31/50 (62%) |
| Answers returned | 38 | 38 |
| Abstentions | 12 | 12 |
| Approved answer accuracy | null | null |

Inspected comparison outputs: Verizon derivatives and MGM EBITDAR supplied
evidence-linked candidate lists and correctly rendered their maximum labels.
JPMorgan no longer returned the previous wrong winner, but abstained: its first
attempt failed quote validation and its repair omitted the mandatory calculations
array. The repaired comparison inputs would select Corporate & Investment Bank,
but the complete response failed the combined schema. This is not a successful answer.

The AMD cash-flow question contains both 'most' and 'least', so direction detection
bypasses comparison validation by design. Do not count it as validated ranking.

Coca-Cola returned 0.80 but still used consolidated net income of 9,571 instead
of the requested shareholder-attributable income. Correct arithmetic and a rounded
numeric match do not establish correct metric selection. The previously reviewed
shareholder-attributable amount is 9,542; both denominators round to 0.80.

Next priorities: resolve combined-schema handling for comparison-only responses,
then validate requested metric selection. Keep source-sign and quote checks strict.
No full answer-accuracy or semantic citation-accuracy percentage is established.
The optional feature remains opt-in; original submission results are unchanged.
