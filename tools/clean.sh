#!/bin/bash

echo "Cleaning..."

latexmk -C

rm -rf build/*

echo "Done!"