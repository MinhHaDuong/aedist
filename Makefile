# aedist/Makefile

PROMPT := prompts/prompt_1_singleshot.txt
MODELS := models.yaml
OUTPUT := outputs/llm_direct

.PHONY: query evaluate

query:
	uv run python -m aedist.query \
	    --prompt $(PROMPT) --models $(MODELS) --output $(OUTPUT)/

evaluate:
	uv run python -m aedist.runner evaluate-all
