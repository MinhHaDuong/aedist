# aedist — AI-driven Energy Data Integration for Sustainable Transition

Benchmark and tools for evaluating AI systems on the production of economic statistics.

## Quick start

```bash
pip install -e .

# Evaluate one system output against the reference
aedist evaluate outputs/llm_direct/claude_sonnet_concise.csv

# Evaluate all available outputs
aedist evaluate-all
```

## Repository structure

```
aedist/
├── src/aedist/                 # Python package
│   ├── schema.py               # Pydantic canonical data model
│   ├── cleaner/                # Config-driven normalization (names, fuels, statuses)
│   │   ├── cleaner.py
│   │   └── config.json
│   ├── matching/               # Matching algorithms
│   │   ├── lp.py               # MILP optimal assignment (default)
│   │   └── phased.py           # Greedy 2-pass (fallback)
│   ├── reconcile.py            # Adapter: Pydantic ↔ LP matching
│   ├── metrics.py              # Coverage, precision, F1, error taxonomy
│   ├── runner.py               # CLI entry point
│   ├── query.py                # Query LLMs via OpenRouter
│   └── convert.py              # Generate LaTeX tables from results
├── data/reference/             # Expert-compiled datasets
│   ├── vietnam_thermal_v1.csv  # Gold standard: 163 plants, canonical schema
│   ├── vietnam_thermal_units_v1.csv  # Unit-level (251 units)
│   └── gem_thermal.csv         # Global Energy Monitor comparison
├── outputs/                    # System outputs (one CSV per run)
│   ├── llm_direct/
│   ├── llm_multiturn/
│   ├── rag_curated/
│   └── rag_extended/
├── results/                    # Evaluation results
├── prompts/                    # Standardized prompts
├── pdfOCR2md/                  # PDF→Markdown conversion tool
├── paper/                      # Benchmark paper source
├── diagrams/                   # Architecture diagrams
├── tests/
├── ADR.md                      # Architecture Decision Records
└── pyproject.toml
```

## Architecture decisions

See [ADR.md](ADR.md) for documented decisions:

1. **Two repos**: Code+bench unified here; LaTeX report separate
2. **MILP matching**: Optimal global assignment via PuLP/CBC
3. **Global matching**: No province×fuel grouping (errors captured as attribute metrics)
4. **Plant-level granularity**: Benchmark operates on plants, not units

## Key results (Claude 3.5 Sonnet)

| Configuration                | Plants | Matched | Coverage | Precision | F1    |
|------------------------------|--------|---------|----------|-----------|-------|
| LLM direct (concise)        |     30 |      30 |    18.4% |    100.0% | 31.1% |
| LLM direct (normal)         |     38 |      38 |    23.3% |    100.0% | 37.8% |
| Multi-turn (+1 relance)     |     72 |      72 |    44.2% |    100.0% | 61.3% |
| RAG curated (no relance)    |     59 |      59 |    36.2% |    100.0% | 53.1% |
| RAG curated + 1 relance     |    100 |     100 |    61.4% |    100.0% | 76.0% |

## License

CC-BY-SA 4.0
