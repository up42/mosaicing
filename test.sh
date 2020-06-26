rm -r .pytest_cache
black .
python -m pytest --pylint --mypy --mypy-ignore-missing-imports --cov=utils/
coverage-badge -f -o coverage.svg
