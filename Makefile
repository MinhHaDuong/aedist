# aedist/Makefile — Reproducible experiment pipeline
#
# Each sweep is defined by a YAML config in sweeps/.
# The Makefile reads the config and calls the appropriate query script.
#
# Usage:
#   make -j8 sweep1          # All OpenRouter + Padme models, 3 runs each
#   make -j4 sweep1-padme    # Padme only
#   make sweep1-summary      # Extract → evaluate → summarize
#   make -j8 sweep2          # All information regimes (requires sweep1 done)
#
# Dependencies tracked: prompt or models change → affected outputs regenerate.

SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c

# --- Read sweep configs via Python helper ------------------------------------
# Usage: $(call cfg,sweep1_census,field)
cfg = $(shell python3 -c "import yaml; c=yaml.safe_load(open('sweeps/$(1).yaml')); print(c.get('$(2)',''))")

# --- Sweep 1: Model census ---------------------------------------------------

S1_PROMPT  := $(call cfg,sweep1_census,prompt)
S1_MODELS  := $(call cfg,sweep1_census,models)
S1_REPEAT  := $(call cfg,sweep1_census,repeat)
S1_BUDGET  := $(call cfg,sweep1_census,budget_usd)
S1_OUTPUT  := $(call cfg,sweep1_census,output)

S1P_MODELS := $(call cfg,sweep1_padme,models)
S1P_URL    := $(call cfg,sweep1_padme,ollama_url)

# One stamp file per model = "this model has been queried"
S1_OR_SHORTS  = $(shell python3 -c "import yaml; ms=yaml.safe_load(open('$(S1_MODELS)')); print(' '.join(m['id'].split('/')[-1].replace(':','-') for m in ms))")
S1_PAD_SHORTS = $(shell python3 -c "import yaml; ms=yaml.safe_load(open('$(S1P_MODELS)')); print(' '.join(m['id'].replace(':','-') for m in ms))")

S1_OR_STAMPS  = $(patsubst %,$(S1_OUTPUT)/.stamp-%,$(S1_OR_SHORTS))
S1_PAD_STAMPS = $(patsubst %,$(S1_OUTPUT)/.stamp-padme-%,$(S1_PAD_SHORTS))

.PHONY: sweep1 sweep1-openrouter sweep1-padme sweep1-summary

sweep1: sweep1-openrouter sweep1-padme

sweep1-openrouter: $(S1_OR_STAMPS)

sweep1-padme: $(S1_PAD_STAMPS)

sweep1-summary:
	uv run python -m aedist.extract --input $(S1_OUTPUT) --output $(S1_OUTPUT)
	uv run python -m aedist.runner evaluate-all --outputs-dir $(S1_OUTPUT)
	@mkdir -p results/sweep1_census
	uv run python scripts/summarize_sweep.py \
	    --metrics results/sweep1_census/all_metrics.json \
	    --queries $(S1_OUTPUT) \
	    --output results/sweep1_census/summary.csv

# OpenRouter: query one model (3 runs), touch stamp
$(S1_OUTPUT)/.stamp-%: $(S1_PROMPT) $(S1_MODELS) sweeps/sweep1_census.yaml
	$(eval FULL_ID := $(shell python3 -c "import yaml; ms=yaml.safe_load(open('$(S1_MODELS)')); hits=[m['id'] for m in ms if m['id'].split('/')[-1].replace(':','-')=='$*']; print(hits[0] if hits else '')"))
	@if [ -z "$(FULL_ID)" ]; then echo "SKIP $*"; exit 0; fi
	uv run python -m aedist.query \
	    --prompt $(S1_PROMPT) --models $(S1_MODELS) \
	    --output $(S1_OUTPUT) --repeat $(S1_REPEAT) \
	    --budget-usd $(S1_BUDGET) --model $(FULL_ID)
	@mkdir -p $(dir $@) && touch $@

# Padme: query one local model (3 runs), touch stamp
$(S1_OUTPUT)/.stamp-padme-%: $(S1_PROMPT) $(S1P_MODELS) sweeps/sweep1_padme.yaml
	$(eval OLLAMA_ID := $(shell python3 -c "import yaml; ms=yaml.safe_load(open('$(S1P_MODELS)')); hits=[m['id'] for m in ms if m['id'].replace(':','-')=='$*']; print(hits[0] if hits else '')"))
	@if [ -z "$(OLLAMA_ID)" ]; then echo "SKIP padme/$*"; exit 0; fi
	uv run python scripts/query_padme.py \
	    --prompt $(S1_PROMPT) --output $(S1_OUTPUT) \
	    --repeat $(S1_REPEAT) --model $(OLLAMA_ID)
	@mkdir -p $(dir $@) && touch $@

# --- Sweep 2: Information regimes (top 5 from sweep 1) -----------------------

S2MT_PROMPT := $(call cfg,sweep2_multiturn,prompt)
S2MT_FOLLOW := $(call cfg,sweep2_multiturn,followups)
S2MT_MODELS := $(call cfg,sweep2_multiturn,models)
S2MT_REPEAT := $(call cfg,sweep2_multiturn,repeat)
S2MT_BUDGET := $(call cfg,sweep2_multiturn,budget_usd)
S2MT_OUTPUT := $(call cfg,sweep2_multiturn,output)

S2R_PROMPT  := $(call cfg,sweep2_rag,prompt)
S2R_CORPUS  := $(call cfg,sweep2_rag,corpus)
S2R_STRAT   := $(call cfg,sweep2_rag,strategy)
S2R_MODELS  := $(call cfg,sweep2_rag,models)
S2R_REPEAT  := $(call cfg,sweep2_rag,repeat)
S2R_BUDGET  := $(call cfg,sweep2_rag,budget_usd)
S2R_OUTPUT  := $(call cfg,sweep2_rag,output)

S2W_PROMPT  := $(call cfg,sweep2_web,prompt)
S2W_MODELS  := $(call cfg,sweep2_web,models)
S2W_REPEAT  := $(call cfg,sweep2_web,repeat)
S2W_BUDGET  := $(call cfg,sweep2_web,budget_usd)
S2W_OUTPUT  := $(call cfg,sweep2_web,output)

.PHONY: sweep2 sweep2-multiturn sweep2-rag sweep2-web

sweep2: sweep2-multiturn sweep2-rag sweep2-web

sweep2-multiturn:
	uv run python -m aedist.query_multiturn \
	    --prompt $(S2MT_PROMPT) --followups $(S2MT_FOLLOW) \
	    --models $(S2MT_MODELS) --output $(S2MT_OUTPUT) \
	    --repeat $(S2MT_REPEAT) --budget-usd $(S2MT_BUDGET)

sweep2-rag:
	uv run python -m aedist.query_rag \
	    --prompt $(S2R_PROMPT) --corpus $(S2R_CORPUS) \
	    --strategy $(S2R_STRAT) --models $(S2R_MODELS) \
	    --output $(S2R_OUTPUT) --repeat $(S2R_REPEAT) \
	    --budget-usd $(S2R_BUDGET)

sweep2-web:
	uv run python -m aedist.query_web \
	    --prompt $(S2W_PROMPT) --models $(S2W_MODELS) \
	    --output $(S2W_OUTPUT) --repeat $(S2W_REPEAT) \
	    --budget-usd $(S2W_BUDGET)

# --- Utility -----------------------------------------------------------------

.PHONY: help clean

help:
	@echo "Sweeps:"
	@echo "  make -j8 sweep1           Census: all models × 3 runs"
	@echo "  make -j4 sweep1-padme     Census: local models only"
	@echo "  make sweep1-summary       Extract + evaluate + summarize"
	@echo "  make sweep2               All information regimes"
	@echo ""
	@echo "Config files in sweeps/*.yaml"

clean:
	rm -f outputs/*/.stamp-*
