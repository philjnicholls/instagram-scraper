define USAGE

Commands:
	init		Install Python dependencies with pip
	test      	Run tests
	test      	Run tests with coverage report
endef

export USAGE
help:
	@echo "$$USAGE"

init:
	pip install -r requirements/common.txt

test:
	PYTHONPATH=. pytest --flake8
test_cov:
	PYTHONPATH=. pytest --flake8 --cov --cov-report term-missing
