# Convenience targets for MedGuard.
.PHONY: install test mcp web demo eval

install:            ## Install dependencies
	pip install -r requirements.txt

test:               ## Run the deterministic test suite (no API key needed)
	PYTHONPATH=. pytest -q

mcp:                ## Run the MCP server standalone (stdio)
	python -m mcp_server.server

demo:               ## Run the offline demo (no API key needed)
	python -m scripts.demo_offline

web:                ## Launch the ADK dev UI (needs GOOGLE_API_KEY)
	adk web

eval:               ## Run the ADK evaluation set (needs GOOGLE_API_KEY)
	adk eval medguard eval/medguard.evalset.json
