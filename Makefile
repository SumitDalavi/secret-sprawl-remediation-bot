.PHONY: install demo

install:
	pip install -r requirements.txt

demo:
	./scripts/run_demo.sh
