# Week 4 Protocol: Does a calculator improve Qwen2.5-3B on multi-step arithmetic?

**System:** `week3_react.py` (Qwen2.5-3B-Instruct, greedy decoding, one calculator tool). **Status:** pre-registered draft; the rules in sections 3 and 4 are fixed before any run.

## Summary

- **Claim:** on multi-step arithmetic word problems, a calculator in a ReAct-style loop improves accuracy over direct answering, at acceptable cost.
- **Pilot (20 tasks):** direct 7/20, ReAct 11/20. That gap is not distinguishable from noise (sign test p of about 0.29).
- **Why the pilot can't be trusted yet:** truncated baseline answers, a tool-interface failure, and a string-based scorer.
- **Proposed test:** three arms on 60 tasks, with a sealed held-out set and a numeric decision rule fixed in advance.

## 1. Claim and scope

On multi-step arithmetic word problems (percentages, rates, unit costs), giving Qwen2.5-3B-Instruct a calculator improves accuracy over answering directly, and the gain is worth the extra cost. One model, one tool, one task family; nothing is claimed beyond that.

## 2. Pilot evidence and audit

| Arm | Correct | 95% interval |
| --- | --- | --- |
| Direct baseline | 7/20 (35%) | 18% to 57% |
| ReAct | 11/20 (55%) | 34% to 74% |

Paired: both correct 5, ReAct only 6, baseline only 2, neither 7. The pilot is suggestive, not evidence. The audit found:

1. **Baseline truncation.** 12 of 13 baseline failures end mid-expression, consistent with the 128-token cap.
2. **Tool-interface failure.** In Q13, Q15 and Q17 the model wrote a correct expression with a stray `}` inside the string. The calculator rejected it twice, and the model then answered from memory and was wrong. It reproduced after the rerun.
3. **Scorer validity.** `is_correct` compares strings, so `94.50` does not match `94.5` (Q06).
4. **Other.** Q19 ran out of steps after malformed output; Q20 needs an unknown `x` the calculator can't solve; 19 of 20 tasks used the tool, so appropriateness is untestable; cost was never recorded.

## 3. Design

*This design is proposed, not built. This week's work is to audit the pilot, to write a protocol, and a lesson memo.*

**Arms.**
- **A. Direct:** no tool, token cap raised to 512.
- **B. Format-matched control:** the same system prompt, JSON format and 3-step budget as C, with the calculator removed so only `final` answers are allowed. This isolates the tool from the format.
- **C. ReAct:** as in Week 3, except that stray trailing `}` characters are stripped from tool-call expressions before calculation, because the pilot showed this caused three failures (Q13, Q15, Q17). When built, the first check is that this fix flips those three tasks (ReAct about 11 to 14 on the pilot set).

**Tasks (60).**
- **Development (40):** the 20 origial tasks, 10 paraphrases, 10 no-tool tasks.
- **Held-out (20):** harder tasks needing two or more dependent calculations, sealed and scored once.
- **Keys:** computed by code and checked by a second person.

**Decoding:** greedy for the main comparison; three sampled runs (temperature 0.7) on the development set to gauge variance.

**Metrics.**
- **Primary:** paired accuracy, C minus B, with a numeric scorer.
- **Secondary:** C minus A; tool-call rate (at least 80% on needs-tool tasks, at most 30% on no-tool tasks); cost as steps and input plus output tokens, counted offline with the Qwen tokenizer; and a failure taxonomy (key error, truncation, tool-interface error, wrong formulation, loop exhaustion, task-tool mismatch).

**Sample size:** about 55 to 60 tasks (McNemar approximation: 20-point gain, 30% disagreement, 5% significance, 80% power). These inputs are uncertain; the pilot's 20 tasks is underpowered.

## 4. Decision rules (fixed in advance)

- **Supported:** C beats B by at least 15 points on development, the paired bootstrap 95% interval excludes zero, mean tokens in C are no more than 1.5 times A, and the held-out set shows the same direction with at least a 10-point gain.
- **Refuted:** C minus B is below 5 points or negative.
- **Inconclusive:** anything else. The response is more tasks or runs, not reinterpretation.

## 5. Threats to validity and what would change my mind

- **Threats:** one model and decoding setting; I authored the tasks (limited by the sealed held-out set and independent keys); prompts differ between arms; tool-call parsing is fragile.
- **Would change my mind:** the held-out gain disappearing, B matching C (the format, not the tool, drove the gain), or many failures traced to key or scorer errors.

## 6. Reproducibility

Code commit hash, model identifier, decoding settings and seeds, the full task file with keys, and raw outputs and traces for every arm, in `week4/<firstname>/`.
