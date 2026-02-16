# aedist — AI-driven Energy Data Integration for Sustainable Transition

Benchmark and tools for evaluating AI systems on the production of economic statistics.
Case study: Vietnam thermal power plant inventory.

minh.ha-duong@cnrs.fr
2026-02-16

## Quick start

```bash
uv sync --extra dev

# Query 16 LLMs via OpenRouter (single-shot, ~$5)
export OPENROUTER_API_KEY=...
make query

# Extract CSV from JSON responses
make extract

# Evaluate all system outputs against reference
make evaluate
```

### Notes

- `make extract` reads the latest dated directory under `outputs/llm_direct/` (e.g. `YYYY-MM-DD/`) and writes one CSV per model into `outputs/llm_direct/`.
- Known issue (not fixed yet): two JSON files currently fail extraction because the embedded table is not parseable as a CSV with a recognizable header:
     - `outputs/llm_direct/2026-02-16/mistral-large-2512.json`
     - `outputs/llm_direct/2026-02-16/mistral-small-3.2-24b-instruct-2506.json`

## Pipeline

```
prompt + models.yaml
        │
        ▼
   query.py          16 models × OpenRouter → JSON (parallel, cached)
        │
        ▼
   extract.py        JSON responses → CSV tables
        │
        ▼
   runner.py          CSV × reference → reconciliation + metrics JSON
        │
        ▼
   results/summary/all_metrics.json
```

## Repository structure

```
aedist/
├── src/aedist/                 # Python package
│   ├── schema.py               # Pydantic canonical data model (Plant, ReconciliationEntry)
│   ├── cleaner/                # Config-driven normalization (names, provinces, fuels)
│   ├── matching/               # MILP optimal assignment (lp.py) + greedy fallback
│   ├── reconcile.py            # Global matching adapter (no province×fuel grouping)
│   ├── metrics.py              # Coverage, precision, F1, attribute accuracy, error taxonomy
│   ├── runner.py               # CLI: aedist evaluate / evaluate-all
│   ├── query.py                # Query LLMs via OpenRouter (parallel, daily cache)
│   └── convert.py              # Generate LaTeX tables from results
├── data/reference/             # Expert-compiled datasets
│   ├── vietnam_thermal_v1.csv  # Gold standard: 163 plants, canonical schema
│   ├── vietnam_thermal_units_v1.csv  # Unit-level (251 units)
│   └── gem_thermal.csv         # Global Energy Monitor comparison
├── outputs/                    # System outputs
│   ├── llm_direct/             # Single-shot responses (JSON + CSV)
│   ├── llm_multiturn/          # Multi-turn (relances)
│   ├── rag_curated/            # RAG with curated corpus
│   └── rag_extended/           # RAG with extended corpus
├── results/                    # Evaluation results
│   ├── reconciliation/         # Per-run reconciliation tables
│   └── summary/                # all_metrics.json
├── prompts/                    # Standardized prompts
├── models.yaml                 # 16 models: US/CN/FR × frontier→edge × open/commercial
├── pdfOCR2md/                  # PDF→Markdown conversion tool
├── paper/                      # Benchmark paper source
├── diagrams/                   # Architecture diagrams
├── tests/                      # Integration + unit tests
├── ADR.md                      # Architecture Decision Records
├── TODO.md                     # Project roadmap
├── Makefile                    # query, extract, evaluate
└── pyproject.toml
```

## Model registry (16 models)

| Class | Models |
|-------|--------|
| Frontier | Claude Sonnet 4.5, Claude Opus 4.6, Gemini 3 Flash, Grok 4.1 Fast, DeepSeek V3.2 |
| Large | Mistral Large 3, Qwen3 235B, Llama 4 Maverick, MiniMax M2.5, Kimi K2.5 |
| Medium | Mistral Medium 3.1, Qwen3 32B, Nemotron 3 Nano 30B |
| Small/Edge | Mistral Small 3.2, Ministral 3 8B, Gemini 2.5 Flash Lite |

Coverage: 🇺🇸 7 · 🇨🇳 5 · 🇫🇷 4 — Open 9 · Commercial 7

## Architecture decisions

See [ADR.md](ADR.md):

1. **Two repos**: Code+bench unified here; LaTeX report separate
2. **MILP matching**: Optimal global assignment via PuLP/CBC
3. **Global matching**: No province×fuel grouping (attribute errors measured separately)
4. **Plant-level granularity**: 163 plants, not 251 units

## Key results (Claude 3.5 Sonnet, legacy data)

| Configuration | Matched | Coverage | Precision | F1 |
|---|---|---|---|---|
| Single-shot (concise) | 30/163 | 18.4% | 100% | 31.1% |
| Single-shot (normal) | 38/163 | 23.3% | 100% | 37.8% |
| Multi-turn (+1 relance) | 72/163 | 44.2% | 100% | 61.3% |
| RAG curated | 59/163 | 36.2% | 100% | 53.1% |
| RAG curated + 1 relance | 100/163 | 61.4% | 100% | 76.0% |

## License

CC-BY-SA 4.0
