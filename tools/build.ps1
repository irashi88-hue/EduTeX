New-Item -ItemType Directory -Force build
New-Item -ItemType Directory -Force output

latexmk `
-xelatex `
-output-directory=build `
main.tex

Copy-Item build/main.pdf output/Grammatica-Tedesca.pdf -Force

Write-Host "Done!"