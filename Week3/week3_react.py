"""
Week 3: ReAct Research Engineering Experiment

Implements a minimal ReAct-style agent using:
- Qwen2.5-3B-Instruct
- A deterministic calculator tool
- Structured tool/final decisions
- Baseline vs ReAct comparison
- JSON result persistence

The model is not instructed to always use the calculator.
It decides whether a tool call is useful.
"""

import ast
import json
import re
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


# ============================================================
# Configuration
# ============================================================

MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

DEFAULT_RESULTS_PATH = Path("week3_react_results.json")

MAX_NEW_TOKENS_BASELINE = 128
MAX_NEW_TOKENS_REACT = 192


# ============================================================
# Calculator Tool
# ============================================================

ALLOWED_OPERATORS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}


def safe_calculate(expression: str) -> str:
    """
    Safely evaluate a restricted arithmetic expression.

    Supported:
    - numbers
    - addition
    - subtraction
    - multiplication
    - division
    - unary +/-

    No Python eval() is used.
    """

    expression = expression.strip()

    if len(expression) > 100:
        return "ERROR: expression is too long."

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return "ERROR: invalid arithmetic expression."

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant) and isinstance(
            node.value, (int, float)
        ):
            return node.value

        if isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.UAdd, ast.USub)
        ):
            value = evaluate(node.operand)

            if isinstance(node.op, ast.UAdd):
                return value

            return -value

        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError

            return ALLOWED_OPERATORS[type(node.op)](left, right)

        raise ValueError("unsupported expression")

    try:
        result = evaluate(tree)

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        return str(result)

    except ZeroDivisionError:
        return "ERROR: division by zero."

    except (ValueError, TypeError, OverflowError):
        return "ERROR: unsupported arithmetic expression."


# ============================================================
# Model Loading
# ============================================================

def load_model(model_name: str = MODEL_NAME):
    """Load tokenizer and causal language model."""

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model_kwargs = {
        "torch_dtype": (
            torch.float16
            if torch.cuda.is_available()
            else torch.float32
        )
    }

    if torch.cuda.is_available():
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        **model_kwargs,
    )

    model.eval()

    return tokenizer, model


# ============================================================
# Text Generation
# ============================================================

def generate(
    tokenizer,
    model,
    messages,
    max_new_tokens: int = 256,
    temperature: float = 0.0,
):
    """Generate a response from the language model."""

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
    )

    if torch.cuda.is_available():
        inputs = {
            key: value.to(model.device)
            for key, value in inputs.items()
        }

    generation_kwargs = {
        "max_new_tokens": max_new_tokens,
        "do_sample": temperature > 0,
        "pad_token_id": tokenizer.eos_token_id,
    }

    if temperature > 0:
        generation_kwargs["temperature"] = temperature

    with torch.no_grad():
        output = model.generate(
            **inputs,
            **generation_kwargs,
        )

    generated = output[0][inputs["input_ids"].shape[1]:]

    return tokenizer.decode(
        generated,
        skip_special_tokens=True,
    ).strip()


# ============================================================
# Baseline: Direct Reasoning
# ============================================================

BASELINE_SYSTEM = """Solve the user's arithmetic problem.

Give the final numerical answer clearly.
Do not use external tools.
"""


def baseline_answer(tokenizer, model, question: str):
    """Generate a direct answer without tool use."""

    messages = [
        {
            "role": "system",
            "content": BASELINE_SYSTEM,
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    return generate(
        tokenizer,
        model,
        messages,
        max_new_tokens=MAX_NEW_TOKENS_BASELINE,
    )


# ============================================================
# ReAct Agent
# ============================================================

REACT_SYSTEM = """You are solving a problem with access to one tool:

calculator(expression)

You must decide whether using the calculator would help.

If you want to use the tool, respond with exactly one JSON object:

{"type": "tool_call", "expression": "<arithmetic expression>"}

If you can answer without using the tool, respond with exactly one JSON object:

{"type": "final", "answer": "<answer>"}

After receiving an Observation from the calculator, decide what to do next.

Do not invent tool observations.
"""


def parse_decision(text: str):
    """
    Extract the first valid JSON decision object from model output.

    Expected formats:

    {"type": "tool_call", "expression": "..."}
    {"type": "final", "answer": "..."}
    """

    decoder = json.JSONDecoder()

    for index, character in enumerate(text):
        if character != "{":
            continue

        try:
            obj, _ = decoder.raw_decode(text[index:])

            if isinstance(obj, dict) and "type" in obj:
                return obj

        except json.JSONDecodeError:
            continue

    return None


def react_answer(
    tokenizer,
    model,
    question: str,
    max_steps: int = 3,
):
    """
    Run a minimal ReAct-style loop.

    The model decides whether to:
    1. call the calculator,
    2. receive an observation,
    3. continue,
    4. or provide a final answer.
    """

    messages = [
        {
            "role": "system",
            "content": REACT_SYSTEM,
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    trace = []
    tool_calls = 0

    for step in range(max_steps):

        response = generate(
            tokenizer,
            model,
            messages,
            max_new_tokens=MAX_NEW_TOKENS_REACT,
        )

        decision = parse_decision(response)

        trace.append(
            {
                "step": step + 1,
                "model_output": response,
                "decision": decision,
            }
        )

        # ----------------------------------------------------
        # Invalid model output
        # ----------------------------------------------------

        if decision is None:

            messages.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        'Return exactly one JSON object with either '
                        '"type": "tool_call" or "type": "final".'
                    ),
                }
            )

            continue

        decision_type = decision.get("type")

        # ----------------------------------------------------
        # Final answer
        # ----------------------------------------------------

        if decision_type == "final":

            return {
                "answer": decision.get("answer", ""),
                "trace": trace,
                "tool_calls": tool_calls,
            }

        # ----------------------------------------------------
        # Tool call
        # ----------------------------------------------------

        if decision_type == "tool_call":

            expression = str(
                decision.get("expression", "")
            ).strip()

            if not expression:
                messages.append(
                    {
                        "role": "assistant",
                        "content": response,
                    }
                )

                messages.append(
                    {
                        "role": "user",
                        "content": (
                            'The tool call had no expression. '
                            'Return a valid calculator expression '
                            'or a final answer.'
                        ),
                    }
                )

                continue

            observation = safe_calculate(expression)

            tool_calls += 1

            trace[-1]["action"] = expression
            trace[-1]["observation"] = observation

            messages.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": f"Observation: {observation}",
                }
            )

            continue

        # ----------------------------------------------------
        # Unknown decision type
        # ----------------------------------------------------

        messages.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

        messages.append(
            {
                "role": "user",
                "content": (
                    'Unknown decision type. Return either '
                    '"tool_call" or "final".'
                ),
            }
        )

    return {
        "answer": "NO FINAL ANSWER",
        "trace": trace,
        "tool_calls": tool_calls,
    }


# ============================================================
# Evaluation
# ============================================================

def normalise_answer(text):
    """
    Extract the final numerical value from model output.

    The last numerical value is treated as the predicted answer.
    """

    text = str(text).replace(",", "")

    matches = re.findall(
        r"-?\d+(?:\.\d+)?",
        text,
    )

    return matches[-1] if matches else None


def is_correct(prediction, expected):
    """Check whether the predicted numerical answer matches the expected answer."""

    predicted = normalise_answer(prediction)
    expected = normalise_answer(expected)

    return predicted == expected


# ============================================================
# Experiment Runner
# ============================================================

def run_experiment(
    tokenizer,
    model,
    tasks=None,
    results_path=DEFAULT_RESULTS_PATH,
):
    """
    Run baseline and ReAct experiments on the same task set.

    Results are saved as JSON for persistence across Colab sessions.
    """

    if tasks is None:
        tasks = TASKS

    results = []

    for task in tasks:

        print(f"Running {task['id']}...")

        # ----------------------------------------------------
        # Baseline
        # ----------------------------------------------------

        baseline = baseline_answer(
            tokenizer,
            model,
            task["question"],
        )

        baseline_correct = is_correct(
            baseline,
            task["answer"],
        )

        # ----------------------------------------------------
        # ReAct
        # ----------------------------------------------------

        react = react_answer(
            tokenizer,
            model,
            task["question"],
        )

        react_correct = is_correct(
            react["answer"],
            task["answer"],
        )

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        results.append(
            {
                "id": task["id"],
                "question": task["question"],
                "expected": task["answer"],
                "baseline_answer": baseline,
                "baseline_correct": baseline_correct,
                "react_answer": react["answer"],
                "react_correct": react_correct,
                "tool_calls": react["tool_calls"],
                "trace": react["trace"],
            }
        )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    results_path = Path(results_path)

    with results_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nResults saved to: {results_path}")

    return results


# ============================================================
# Results Utilities
# ============================================================

def results_to_dataframe(results):
    """Convert experiment results into a compact DataFrame."""

    rows = []

    for result in results:
        rows.append(
            {
                "id": result["id"],
                "expected": result["expected"],
                "baseline_answer": result["baseline_answer"],
                "baseline_correct": result["baseline_correct"],
                "react_answer": result["react_answer"],
                "react_correct": result["react_correct"],
                "tool_calls": result["tool_calls"],
            }
        )

    return pd.DataFrame(rows)


def summarise_results(results):
    """Return aggregate baseline/ReAct accuracy and tool-use statistics."""

    df = results_to_dataframe(results)

    baseline_accuracy = df["baseline_correct"].mean()
    react_accuracy = df["react_correct"].mean()

    tool_use_rate = (
        (df["tool_calls"] > 0).mean()
    )

    average_tool_calls = df["tool_calls"].mean()

    return {
        "baseline_accuracy": baseline_accuracy,
        "react_accuracy": react_accuracy,
        "tool_use_rate": tool_use_rate,
        "average_tool_calls": average_tool_calls,
    }