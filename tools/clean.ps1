Write-Host ""
Write-Host "====================================="
Write-Host " Cleaning project"
Write-Host "====================================="

if (Test-Path build) {
    Remove-Item build\* -Recurse -Force
}

if (Test-Path output\Grammatica-Tedesca.pdf) {
    Remove-Item output\Grammatica-Tedesca.pdf -Force
}

Write-Host ""
Write-Host "Project cleaned."