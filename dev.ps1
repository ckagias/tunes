# Runs both the FastAPI backend and the Vite frontend for local development,
# both in this one window with interleaved output. Ctrl+C stops both.

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Switch the console's active code page to UTF-8 so Vite's box-drawing arrow (➜)
# renders correctly instead of as mangled bytes under the default OEM code page.
chcp 65001 >$null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$backend = Start-Job -ScriptBlock {
    param($root)
    chcp 65001 >$null
    $OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Set-Location "$root\backend"
    & .\.venv\Scripts\Activate.ps1
    uvicorn app.main:app --reload --port 8000 2>&1
} -ArgumentList $root

$frontend = Start-Job -ScriptBlock {
    param($root)
    chcp 65001 >$null
    $OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Set-Location "$root\frontend"
    npm run dev 2>&1
} -ArgumentList $root

try {
    while ($true) {
        Receive-Job $backend, $frontend | ForEach-Object { Write-Host $_ }
        if ($backend.State -ne 'Running' -and $frontend.State -ne 'Running') {
            break
        }
        Start-Sleep -Milliseconds 300
    }
}
finally {
    Write-Host "`nStopping dev servers..."
    Stop-Job $backend, $frontend -ErrorAction SilentlyContinue
    Remove-Job $backend, $frontend -Force -ErrorAction SilentlyContinue
}
