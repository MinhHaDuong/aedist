"""Query LLMs via OpenRouter and save results.

Usage:
    python -m aedist.query --prompt prompts/prompt1.txt \
                           --models models.yaml \
                           --output outputs/sweep1/
    python -m aedist.query --prompt prompts/prompt1.txt \
                           --models models.yaml \
                           --output outputs/sweep1/ \
                           --model deepseek/deepseek-r1 \
                           --repeat 3 --budget-usd 5
"""

import argparse
import json
import logging
import os
import time
from datetime import date
from pathlib import Path

import yaml
from openai import OpenAI

log = logging.getLogger(__name__)


def load_models(path: str) -> list[dict]:
    with open(path) as f:
        return yaml.safe_load(f)


def compute_cost(usage: dict, model: dict) -> float:
    """Compute USD cost from token usage and model pricing."""
    price_in = model.get("price_per_mtok_in", 0.0)
    price_out = model.get("price_per_mtok_out", 0.0)
    prompt_tokens = usage.get("prompt_tokens", 0) or 0
    completion_tokens = usage.get("completion_tokens", 0) or 0
    return (prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000


def model_metadata(model: dict) -> dict:
    """Extract metadata fields from model registry entry."""
    return {
        k: model.get(k)
        for k in ("size_class", "country", "architecture", "provider", "context_window")
        if model.get(k) is not None
    }


def query_model(client: OpenAI, model_id: str, prompt: str) -> dict:
    """Send prompt to a model via OpenRouter, return response dict with timing."""
    t0 = time.monotonic()
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
    )
    wall_seconds = round(time.monotonic() - t0, 3)
    choice = response.choices[0]
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
    }
    return {
        "response": choice.message.content,
        "finish_reason": choice.finish_reason,
        "usage": usage,
        "wall_seconds": wall_seconds,
    }


def output_filename(model_id: str, run: int) -> str:
    """Generate output filename: {short_name}-run{n}.json."""
    short = model_id.split("/")[-1]
    return f"{short}-run{run}.json"


def save_result(
    output_dir: Path,
    model_id: str,
    prompt: str,
    result: dict,
    run: int,
    model: dict,
) -> Path:
    """Save query result as JSON with operational metrics."""
    day_dir = output_dir / date.today().isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)

    filepath = day_dir / output_filename(model_id, run)

    usage = result.get("usage") or {}
    cost = compute_cost(usage, model) if usage else 0.0

    record = {
        "model": model_id,
        "date": date.today().isoformat(),
        "run": run,
        "prompt": prompt,
        "wall_seconds": result.get("wall_seconds", 0.0),
        "cost_usd": cost,
        "model_metadata": model_metadata(model),
        **{k: v for k, v in result.items() if k not in ("wall_seconds",)},
    }

    with open(filepath, "w") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    log.info("Saved %s", filepath)
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Query LLMs via OpenRouter")
    parser.add_argument("--prompt", required=True, help="Path to prompt text file")
    parser.add_argument("--models", required=True, help="Path to models.yaml")
    parser.add_argument("--output", required=True, help="Output directory for results")
    parser.add_argument("--model", help="Query only this model (OpenRouter ID)")
    parser.add_argument("--repeat", type=int, default=1, help="Number of runs per model")
    parser.add_argument("--budget-usd", type=float, default=None, help="Stop if cumulative cost exceeds budget")
    parser.add_argument("--dry-run", action="store_true", help="List what would be queried, don't call API")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    prompt = Path(args.prompt).read_text().strip()
    models = load_models(args.models)
    output_dir = Path(args.output)

    # Filter to single model if requested
    if args.model:
        models = [m for m in models if m["id"] == args.model]
        if not models:
            raise SystemExit(f"Model {args.model} not found in {args.models}")

    if args.dry_run:
        for model in models:
            for run in range(1, args.repeat + 1):
                log.info("Would query %s run %d", model["id"], run)
        return

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENROUTER_API_KEY environment variable")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    total_cost = 0.0

    for model in models:
        model_id = model["id"]
        label = model.get("name", model_id)

        for run in range(1, args.repeat + 1):
            # Budget guard
            if args.budget_usd is not None and total_cost >= args.budget_usd:
                log.warning(
                    "Budget exceeded (%.4f >= %.4f USD). Stopping.",
                    total_cost, args.budget_usd,
                )
                return

            # Skip if already exists
            day_dir = output_dir / date.today().isoformat()
            filepath = day_dir / output_filename(model_id, run)
            if filepath.exists():
                log.info("Skip %s run %d (cached)", label, run)
                continue

            log.info("Querying %s run %d/%d...", label, run, args.repeat)
            try:
                result = query_model(client, model_id, prompt)
                save_result(output_dir, model_id, prompt, result, run, model)
                usage = result.get("usage") or {}
                cost = compute_cost(usage, model)
                total_cost += cost
                log.info("  Done. cost=%.6f total=%.6f USD", cost, total_cost)
            except Exception as e:
                log.error("Error querying %s run %d: %s", label, run, e)
                save_result(output_dir, model_id, prompt, {
                    "response": None,
                    "finish_reason": "error",
                    "error": str(e),
                    "usage": None,
                }, run, model)

    log.info("Completed. Total cost: %.6f USD", total_cost)


if __name__ == "__main__":
    main()
