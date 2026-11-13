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

import io
import contextlib
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


import ast


import subprocess

def safe_python_exec(code: str) -> str:
    """
    Execute Python code for mathematical and computational tasks.

    Convenience restrictions only; this is NOT a secure sandbox.
    """

    if len(code) > 5000:
        return "ERROR: code is too long."

    blocked_names = {
        "os", "sys", "subprocess", "shutil",
        "socket", "requests", "urllib",
        "importlib", "pathlib", "builtins",
        "open", "eval", "exec", "compile",
        "globals", "locals", "getattr",
        "setattr", "delattr", "__import__"
    }

    try:
        tree = ast.parse(code, mode="exec")

        if sum(1 for _ in ast.walk(tree)) > 500:
            return "ERROR: code is too complex."

        for node in ast.walk(tree):

            if isinstance(node, (ast.Import, ast.ImportFrom)):
                raise ValueError("Imports are not allowed.")

            if isinstance(node, ast.Name):
                if node.id in blocked_names:
                    raise ValueError(
                        f"Restricted name: {node.id}"
                    )

            if isinstance(node, ast.Attribute):
                if node.attr.startswith("__"):
                    raise ValueError(
                        "Dunder attributes are not allowed."
                    )

        # Automatically display the last expression.
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            last_expression = tree.body[-1].value

            already_printing = (
                isinstance(last_expression, ast.Call)
                and isinstance(last_expression.func, ast.Name)
                and last_expression.func.id == "print"
            )

            if not already_printing:
                tree.body[-1] = ast.Expr(
                    value=ast.Call(
                        func=ast.Name(id="print", ctx=ast.Load()),
                        args=[last_expression],
                        keywords=[]
                    )
                )

        ast.fix_missing_locations(tree)

        # Shared namespace fixes comprehension NameError.
        namespace = {
            "__builtins__": {},
            "range": range,
            "min": min,
            "max": max,
            "sum": sum,
            "len": len,
            "all": all,
            "any": any,
            "int": int,
            "float": float,
            "str": str,
            "abs": abs,
            "round": round,
            "print": print,
        }

        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exec(
                compile(tree, "<python-tool>", "exec"),
                namespace,
                namespace
            )

        result = output.getvalue().strip()

        return result if result else "Execution completed."

    except Exception as error:
        return f"ERROR: {type(error).__name__}: {error}"
        
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

REACT_SYSTEM = """
You are solving this problem with access to two tools:

1. calculator(expression):
   Use for basic arithmetic: addition, subtraction,
   multiplication and division.

2. python(expression):
   Use for more complex mathematical operations,
   such as counting divisors using range() and len().

Decide which tool is appropriate.

For calculator:
{"type": "tool_call", "tool": "calculator", "expression": "10 + 5"}

For Python:
{"type": "tool_call", "tool": "python", "expression": "len([i for i in range(1, 197) if 196 % i == 0])"}

For final answer:
{"type": "final", "answer": "15"}

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
                messages.append({
                    "role": "assistant",
                    "content": response,
                })

                messages.append({
                    "role": "user",
                    "content": (
                        "The tool call had no expression. "
                        "Return a valid tool call or final answer."
                    ),
                })

                continue

            tool_name = decision.get("tool", "calculator")

            if tool_name == "calculator":
                observation = safe_calculate(expression)

            elif tool_name == "python":
                observation = safe_python_exec(expression)

            else:
                observation = "ERROR: unknown tool."

            tool_calls += 1

            trace[-1]["tool"] = tool_name
            trace[-1]["action"] = expression
            trace[-1]["observation"] = observation

            # Append the assistant's tool request
            messages.append({
                "role": "assistant",
                "content": response,
            })

            # Handle errors
            if observation.startswith("ERROR"):
                messages.append({
                    "role": "user",
                    "content": (
                        f"Tool execution failed: {observation}. "
                        "Your Python tool supports only explicitly permitted "
                        "operations. Do not repeat the same expression. "
                        "Break the calculation into simpler supported steps "
                        "or provide a final answer."
                    ),
                })

                continue

            # Return successful observation
            messages.append({
                "role": "user",
                "content": f"Observation: {observation}",
            })

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