.PHONY: run test clean

run:
	python3 run_pipeline.py

test:
	python3 -m unittest discover -s tests -v

clean:
	rm -f data/product_analytics.db data/raw/*.csv data/processed/*.csv reports/*.html reports/*.json

