# Week 2: In-context learning and prompt format

This submission uses `Qwen/Qwen2.5-0.5B-Instruct` to explore how examples and their format affect structured JSON extraction from a fixed travel-booking message.

## Notebook

- [`week2_in_context_learning.ipynb`](week2_in_context_learning.ipynb)
- [Kaggle run](https://www.kaggle.com/code/chuloway/testing-out-in-context-learning)

## Observations

| Prompt condition | Observed output |
|---|---|
| Zero-shot | Extracted all four fields, but wrapped the object in a Markdown JSON fence and used title-case keys. |
| One-shot | Produced a bare JSON object and followed the example's lowercase key format. |
| Three examples with a non-JSON example last | Still produced JSON, suggesting the explicit instruction outweighed the conflicting recent format in this run. |

The one-shot example most clearly improved schema and formatting consistency. The recency test did not overturn the requested JSON format for this prompt.

## Limitations

- Each condition was run on one input, so the notebook is a qualitative demonstration rather than a scored evaluation.
- Example count, order, and format are not varied independently across repeated trials.
- Sampling uses `do_sample=True`; without fixed seeds, exact outputs may vary between runs.
- The experiment uses one small instruction-tuned model, so the observations should not be generalized to other models.
