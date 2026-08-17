.PHONY: install install-dev test run up down lint seed

install:        ## Install full dependencies
	pip install -r requirements.txt

install-dev:    ## Install minimal test dependencies
	pip install -r requirements-dev.txt

test:           ## Run unit tests
	PYTHONPATH=src pytest tests/ -q

run:            ## Run Streamlit app locally
	PYTHONPATH=src streamlit run app/streamlit_app.py

up:             ## Start full stack (app + postgres + neo4j)
	docker compose up --build

down:           ## Stop the stack
	docker compose down

seed:           ## Load demo data into Postgres + Neo4j
	PYTHONPATH=src python scripts/seed_demo_data.py
