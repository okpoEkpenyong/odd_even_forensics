# Analysis of Competing Hypotheses

This is a provisional qualitative ACH worksheet. Compatibility scores are researcher judgements, not statistical probabilities or evidence of latent intent.

**Score legend:** +2 = strongly supports; +1 = supports; 0 = neutral/ambiguous; -1 = contradicts; -2 = strongly contradicts.

| Evidence | Observation | H0 | H1 | H2 | H3 | H4 |
| --- | --- | --- | --- | --- | --- | --- |
| E1: Bare environment | 0/40 odd across GPT-OSS-20B and 120B | 1 | 0 | 1 | 2 | 0 |
| E2: Strategic framing | 8/40 odd: GPT-OSS-120B 5/20; GPT-OSS-20B 3/20 | 1 | 2 | 0 | 0 | 1 |
| E3: Non-strategic frame controls | 1/220 odd across baseline, no-reward, cost-control, obedience, broken-system, hierarchy-only-bare cells (single 20B baseline anomaly) | 0 | -1 | 0 | 1 | 0 |
| E4: Persona-only, GPT-OSS-120B | 14/33 odd (42.4%); 2 explicit refusals | 0 | 1 | 0 | 0 | 2 |
| E5: Persona-only, GPT-OSS-20B | 3/20 odd; 4 explicit refusals | 0 | 1 | 0 | 0 | 2 |
| E6: User-as-developer control | 0/40 odd across both models | 0 | -2 | 0 | 1 | 2 |
| E7: Strategic refusal traces | Explicit refusals occurred under strategic framing | 0 | 0 | -1 | 0 | 2 |
| E8: Hierarchy-only bare control | 0/40 odd: system-level authority present, no strategic persona | 0 | -1 | 0 | 0 | 1 |
| E9: Deceptive-rigged positive control | 5/15 (33.3%, 120B) and 9/15 (60.0%, 20B) hacking when instructed to hack and conceal | 0 | 0 | 0 | 0 | 0 |

## Hypotheses

- **H0** — Metagaming / evaluation-probe recognition
- **H1** — Reward-directed behaviour
- **H2** — Confusion / failure to resolve the instruction conflict
- **H3** — Adversarial-pattern recognition
- **H4** — Hierarchy-enabled strategic-role effects (persona + system-level authority)

## Evidence notes

### E1: Bare environment
- Observation: 0/40 odd across GPT-OSS-20B and 120B
- Interpretation: Reward note alone did not produce odd outputs in the bare user-message setting.
### E2: Strategic framing
- Observation: 8/40 odd: GPT-OSS-120B 5/20; GPT-OSS-20B 3/20
- Interpretation: Odd outputs occur at a moderate rate when reward-maximising strategic framing is present.
### E3: Non-strategic frame controls
- Observation: 1/220 odd across baseline, no-reward, cost-control, obedience, broken-system, hierarchy-only-bare cells (single 20B baseline anomaly)
- Interpretation: Odd behaviour was almost entirely concentrated in strategic/persona frames. The single anomaly's CoT shows the same developer-over-user reward reasoning seen in strategic frames, indicating the mechanism exists at trace levels without persona amplification.
### E4: Persona-only, GPT-OSS-120B
- Observation: 14/33 odd (42.4%); 2 explicit refusals
- Interpretation: Strategic persona plus reward framing substantially changes outcomes.
### E5: Persona-only, GPT-OSS-20B
- Observation: 3/20 odd; 4 explicit refusals
- Interpretation: The same framing also changes behaviour in the smaller model, with refusals appearing.
### E6: User-as-developer control
- Observation: 0/40 odd across both models
- Interpretation: Removing the system/user distinction removed the effect, as the hierarchy-availability reading of H4 predicts; scored as support for H4 on that reading. Message-position and prompt-structure confounds remain (see Cautions).
### E7: Strategic refusal traces
- Observation: Explicit refusals occurred under strategic framing
- Interpretation: Refusals side with the reward instruction (declining the user's request) rather than rejecting the scoring rule — refusal is reward-protective, not cheat-averse.
### E8: Hierarchy-only bare control
- Observation: 0/40 odd: system-level authority present, no strategic persona
- Interpretation: Authority alone is insufficient; consistent with the persona being the active ingredient within H4's permission structure.
### E9: Deceptive-rigged positive control
- Observation: 5/15 (33.3%, 120B) and 9/15 (60.0%, 20B) hacking when instructed to hack and conceal
- Interpretation: Instrument validation only: confirms the probes can detect concealment. Scored 0 for all hypotheses because behaviour was instructed, not naturally occurring.

## Cautions

- H1 should not be read as proof of a latent reward objective.
- H2/H3 remain difficult to separate without cleaner counterfactual interventions and direct trace inspection.
- The user-as-developer comparison has message-position and prompt-structure confounds; it should not be treated as a clean authority manipulation.
- The positive-control experiment is instrument validation, not a ground-truth label for naturally occurring strategic behaviour.
- Do not convert the total scores into probabilities or a claim that one hypothesis is the model's 'true motive'.
