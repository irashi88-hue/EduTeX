# ==========================
# German Grammar Book
# ==========================

.PHONY: build clean release help

build:
	latexmk -r tools/latexmkrc main.tex

release: build
	@echo "Release ready."

clean:
	latexmk -C
	@echo "Cleaning build directory..."
	@if [ -d build ]; then rm -rf build/*; fi
	@if [ -d output ]; then rm -f output/*.pdf; fi

help:
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "  make build    Compile the book"
	@echo "  make clean    Remove temporary files"
	@echo "  make release  Compile release version"