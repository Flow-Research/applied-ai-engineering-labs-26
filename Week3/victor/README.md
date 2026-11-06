# Week 3: Minimal ReAct-style tool loop

This submission implements a small ReAct-style loop around `Qwen/Qwen2.5-0.5B-Instruct`. The model can request a deterministic population lookup, receive the observation, and then produce a final answer.

## Notebook

- [`week3_react_loop.ipynb`](week3_react_loop.ipynb)
- [Kaggle run](https://www.kaggle.com/code/chuloway/react-loop-thinking)

## Loop

1. Send the system instructions and user question to the model.
2. Detect an `Action:` response and parse its `Input:` city.
3. Call the local `get_population` tool.
4. Append the tool observation to the conversation.
5. Continue until the model emits `Final Answer:` or reaches the three-turn limit.

## Observations

Both tested prompts successfully requested the lookup tool and returned the tool's `15 million people` observation for Lagos. The one-shot prompt produced a more direct tool-use trace, but the nominal zero-shot “failure case” also used the tool correctly in the saved run.

## Limitations

- The tool accepts only a small hard-coded city set and uses case-sensitive substring matching.
- Tool requests are parsed with string splitting rather than a validated schema.
- The broad exception handler hides the specific parsing error.
- The notebook tests one question, so it does not measure task-level accuracy or tool-use reliability.
- The model's visible `Thought:` text is treated as a protocol marker, not evidence that the trace faithfully represents its internal reasoning.
