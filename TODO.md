# AEDIST — TODO

## Pipeline gaps (blocking evaluation of new models)

- [x] **extract.py**: Parse CSV/table from JSON responses (query output → clean CSV)
      Implemented in `python -m aedist.extract` and writes canonical columns:
      `name,fuel,status,cod,province,capacity_mwe`.
- [x] **Makefile target `extract`**: wired between `query` and `evaluate`
- [x] **evaluate-all on new data**: `make evaluate` now includes extracted CSVs

### Known extraction issues (not fixed yet)

- [ ] Two JSON responses contain a table that is not reliably parseable as CSV (missing/odd header), so `aedist.extract` currently fails:
      - `outputs/llm_direct/2026-02-16/mistral-large-2512.json`
      - `outputs/llm_direct/2026-02-16/mistral-small-3.2-24b-instruct-2506.json`
      (Leave as-is for now; track and handle later.)

## Query configurations (beyond single-shot)

- [ ] **Multi-turn script** (`query_multiturn.py`): send response back + "continue, you're missing plants"
      Loop up to N relances, save each round. Needs conversation history management.
- [ ] **RAG query script** (`query_rag.py`): inject curated docs into system prompt before asking.
      Corpus in `pdfOCR2md/prod/*.md` — concatenate and inject as system context.
- [ ] **Prompt 2** (structured): add to `prompts/prompt_2_structured.txt`
      Ask for specific columns: Name, Province, Fuel, Capacity, Status, COD

## Reference dataset

- [ ] Add COD (commissioning date) column to `vietnam_thermal_v1.csv` where available
- [ ] Cross-validate against GEM dataset (`gem_thermal.csv`)
- [ ] Document data provenance in `data/reference/README.md`

## Metrics & analysis

- [ ] Capacity-weighted coverage (MW recovered / MW total)
- [ ] Per-status breakdown (operational vs planned vs cancelled)
- [ ] Per-fuel breakdown (coal vs gas vs oil)
- [ ] Cost analysis: $/plant-identified by model × configuration
- [ ] Token usage analysis from JSON metadata

## Paper (paper/)

- [ ] Fill Section 5 (Results) with 16-model single-shot results
- [ ] Add multi-turn and RAG comparative tables
- [ ] Barplots: coverage by model, by size class, by country
- [ ] Scatter: coverage vs cost, coverage vs model size
- [ ] Write Section 6 (Discussion) and Section 7 (Conclusion)

## Technical report alignment

- [ ] Update Makefile in report to read from `aedist/results/summary/`
- [ ] Connect `convert.py` to `all_metrics.json` (replace hardcoded data)
- [ ] Merge chapters 2+3 as per TODO.md in report repo

## Code quality

- [ ] Suppress cleaner INFO logging during evaluate (use WARNING level)
- [ ] Add `--verbose` / `--quiet` flags to runner
- [ ] Type-check with mypy
- [ ] Add `conftest.py` with shared fixtures
- [ ] CI: GitHub Actions running `uv run pytest`
