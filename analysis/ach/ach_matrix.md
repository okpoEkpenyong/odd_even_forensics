# Analysis of Competing Hypotheses

This is a provisional qualitative ACH worksheet. Compatibility scores are researcher judgements, not statistical probabilities or evidence of latent intent.

**Score legend:** +2 = strongly supports; +1 = supports; 0 = neutral/ambiguous; -1 = contradicts; -2 = strongly contradicts.

| Evidence | Observation | H0 | H1 | H2 | H3 | H4 |
| --- | --- | --- | --- | --- | --- | --- |
| E1: Bare environment | 1 | 0 | 1 | 2 | 0 |
| E2: Strategic framing | 1 | 2 | 0 | 0 | 1 |
| E3: Non-strategic frame controls | 0 | -1 | 0 | 1 | 0 |
| E4: Persona-only, GPT-OSS-120B | 0 | 1 | 0 | 0 | 2 |
| E5: Persona-only, GPT-OSS-20B | 0 | 1 | 0 | 0 | 2 |
| E6: User-as-developer control | 0 | -2 | 0 | 1 | -2 |
| E7: Strategic refusal traces | 0 | 0 | -1 | 0 | 2 |

## Hypotheses

- **H0** — Metagaming / evaluation-probe recognition
- **H1** — Reward-directed behaviour
- **H2** — Confusion / failure to resolve the instruction conflict
- **H3** — Adversarial-pattern recognition
- **H4** — Persona-driven refusal / strategic-role effects

## Evidence notes

### E1: Bare environment
- Observation: 0/40 odd across GPT-OSS-20B and 120B
- Interpretation: Reward note alone did not produce odd outputs in the bare user-message setting.
### E2: Strategic framing
- Observation: 7/40 odd: GPT-OSS-120B 4/20; GPT-OSS-20B 3/20
- Interpretation: Odd outputs occur at a moderate rate when reward-maximising strategic framing is present.
### E3: Non-strategic frame controls
- Observation: 0/100 odd across baseline, no-reward, cost-control, obedience, broken-system cells
- Interpretation: The observed odd behaviour was concentrated in the strategic frame.
### E4: Persona-only, GPT-OSS-120B
- Observation: 8/20 odd; 2 explicit refusals
- Interpretation: Strategic persona plus reward framing substantially changes outcomes.
### E5: Persona-only, GPT-OSS-20B
- Observation: 4/20 odd; 4 explicit refusals
- Interpretation: The same framing also changes behaviour in the smaller model, with refusals appearing.
### E6: User-as-developer control
- Observation: 0/40 odd across both models
- Interpretation: Moving the substantive framing into one user message removed the observed odd behaviour; authority and message-structure are confounded.
### E7: Strategic refusal traces
- Observation: Explicit refusals occurred under strategic framing
- Interpretation: Some trajectories appear to treat the conflict as a reason to refuse rather than simply output an odd number.

## Cautions

- H1 should not be read as proof of a latent reward objective.
- H2/H3 remain difficult to separate without cleaner counterfactual interventions and direct trace inspection.
- The user-as-developer comparison has message-position and prompt-structure confounds; it should not be treated as a clean authority manipulation.
- The positive-control experiment is instrument validation, not a ground-truth label for naturally occurring strategic behaviour.
- Do not convert the total scores into probabilities or a claim that one hypothesis is the model's 'true motive'.

## Strengths of this Investigation:

- Causal Disentanglement: Unlike standard benchmarks, this project isolated the "Active Ingredient" of hacking by separating the Persona Nudge from the Authority Hierarchy.
- Instrument Validation: Addressing a self-identified gap in the baseline paper (Singh et al., 2026), I successfully implemented a positive control (deceptive_rigged) to verify the recall of the detection probes.
- Statistical Stabilization: By identifying and resolving the N=5 sampling noise, the project established a properly-powered baseline at N=20, allowing for more confident claims about model-scaling differences.