PYTHON ?= python
.PHONY: all data train evaluate clean test api demo
all:
	$(PYTHON) -m src.pipeline all
data:
	$(PYTHON) -m src.pipeline data
train:
	$(PYTHON) -m src.pipeline train
evaluate:
	$(PYTHON) -m src.pipeline evaluate
test:
	$(PYTHON) -m pytest -q
api:
	$(PYTHON) -m uvicorn api.app:app --host 127.0.0.1 --port 8000
demo:
	$(PYTHON) -m streamlit run app.py
clean:
	$(PYTHON) -m src.clean
