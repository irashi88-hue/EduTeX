#!/bin/bash

set -e

echo "====================================="
echo " Building German Grammar PDF"
echo "====================================="

mkdir -p build
mkdir -p output

latexmk \
    -xelatex \
    -interaction=nonstopmode \
    -synctex=1 \
    -file-line-error \
    -output-directory=build \
    main.tex

cp build/main.pdf output/Grammatica-Tedesca.pdf

echo ""
echo "Build completed!"
echo "PDF saved in output/"