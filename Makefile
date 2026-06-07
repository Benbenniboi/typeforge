.PHONY: run build-mac build-win build-linux clean lint

run:
	cd typeforge && python3 main.py

build-mac:
	bash typeforge/packaging/build_mac.sh

build-win:
	typeforge\\packaging\\build_windows.bat

build-linux:
	bash typeforge/packaging/build_linux.sh

clean:
	rm -rf typeforge/dist typeforge/build typeforge/__pycache__
	find typeforge -name "*.pyc" -delete
	find typeforge -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

lint:
	cd typeforge && python3 -m ruff check .
