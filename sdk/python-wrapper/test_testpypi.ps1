# PowerShell script to test uploading to Test PyPI and installing from it
# This simulates the real PyPI experience

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Testing SDK on Test PyPI" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Check if twine is installed
try {
    $null = Get-Command twine -ErrorAction Stop
} catch {
    Write-Host "Error: twine is not installed. Installing..." -ForegroundColor Yellow
    pip install twine
}

# Check if package is built
if (-not (Test-Path "dist\semantis_cache-1.0.0-py3-none-any.whl")) {
    Write-Host "Building package..." -ForegroundColor Yellow
    python -m build
}

Write-Host ""
Write-Host "1. Uploading to Test PyPI..." -ForegroundColor Cyan
Write-Host "   (You will need Test PyPI credentials)" -ForegroundColor Yellow
Write-Host ""
Write-Host "   Test PyPI URL: https://test.pypi.org/" -ForegroundColor White
Write-Host "   Test PyPI Upload URL: https://test.pypi.org/legacy/" -ForegroundColor White
Write-Host ""
Write-Host "   To create Test PyPI account:" -ForegroundColor Yellow
Write-Host "   1. Go to https://test.pypi.org/account/register/" -ForegroundColor White
Write-Host "   2. Create an account" -ForegroundColor White
Write-Host "   3. Generate an API token at https://test.pypi.org/manage/account/token/" -ForegroundColor White
Write-Host ""
Write-Host "   Then use:" -ForegroundColor Yellow
Write-Host "   twine upload --repository testpypi dist/*" -ForegroundColor Green
Write-Host ""
Write-Host "   Username: __token__" -ForegroundColor Cyan
Write-Host "   Password: <your-api-token>" -ForegroundColor Cyan
Write-Host ""

$continue = Read-Host "Press Enter to show upload command, or 's' to skip and just show instructions"

if ($continue -ne 's') {
    Write-Host ""
    Write-Host "Run this command to upload to Test PyPI:" -ForegroundColor Green
    Write-Host "  twine upload --repository testpypi dist/*" -ForegroundColor White
    Write-Host ""
    Write-Host "After uploading, test installation with:" -ForegroundColor Green
    Write-Host "  pip install --index-url https://test.pypi.org/simple/ semantis-cache" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Test PyPI Instructions Complete" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  - Package built: dist\semantis_cache-1.0.0-py3-none-any.whl" -ForegroundColor White
Write-Host "  - Ready for Test PyPI upload" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Create Test PyPI account (if needed)" -ForegroundColor White
Write-Host "  2. Upload: twine upload --repository testpypi dist/*" -ForegroundColor White
Write-Host "  3. Test install: pip install --index-url https://test.pypi.org/simple/ semantis-cache" -ForegroundColor White
Write-Host "  4. Verify on: https://test.pypi.org/project/semantis-cache/" -ForegroundColor White
Write-Host "  5. If all good, upload to production PyPI: twine upload dist/*" -ForegroundColor White
Write-Host ""

