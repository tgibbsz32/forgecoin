# Offline reopening test for a disposable, DPAPI-backed wallet. No seed output.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$WalletExecutable,
    [Parameter(Mandatory=$true)][string]$BackupPath,
    [Parameter(Mandatory=$true)][string]$WalletDirectory
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Security
$cipher = [IO.File]::ReadAllBytes($BackupPath)
$plain = [Security.Cryptography.ProtectedData]::Unprotect(
    $cipher, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
$passfile = Join-Path $WalletDirectory '.offline-reopen-password'
$process = $null
try {
    $record = [Text.Encoding]::UTF8.GetString($plain) | ConvertFrom-Json
    if ($record.format -ne 'ForgeCoin-local-DPAPI-v1') { throw 'Unexpected encrypted backup' }
    $walletPath = Join-Path $WalletDirectory $record.wallet_name
    if (-not (Test-Path -LiteralPath $walletPath) -or
        -not (Test-Path -LiteralPath (Join-Path $WalletDirectory $record.keys_name))) {
        throw 'Missing offline test wallet files'
    }
    [IO.File]::WriteAllText($passfile,$record.wallet_password,[Text.Encoding]::ASCII)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = [IO.Path]::GetFullPath($WalletExecutable)
    $psi.WorkingDirectory = $WalletDirectory
    $psi.Arguments = '--offline --wallet-file "'+$walletPath+'" --password-file "'+$passfile+'" --log-file NUL --command address'
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.EnvironmentVariables['PATH'] = ('C:\msys64\mingw64\bin;' + $env:PATH)
    $process = [Diagnostics.Process]::Start($psi)
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    for ($i=0;$i -lt 3;$i++) { $process.StandardInput.WriteLine('') }
    $process.StandardInput.Close()
    if (-not $process.WaitForExit(30000)) {
        $process.Kill()
        $process.WaitForExit()
        throw 'Offline wallet reopen timed out'
    }
    $output = $stdout.GetAwaiter().GetResult()
    $null = $stderr.GetAwaiter().GetResult()
    if ($process.ExitCode -ne 0) { throw 'Offline wallet reopen failed' }
    # A standard CryptoNote primary address should be approximately 95 chars.
    $candidates = [regex]::Matches($output,'(?<![1-9A-HJ-NP-Za-km-z])[1-9A-HJ-NP-Za-km-z]{95}(?![1-9A-HJ-NP-Za-km-z])')
    if ($candidates.Count -eq 0) { throw 'Offline wallet did not emit a primary address' }
    $address = $candidates[0].Value
    $file = Join-Path $WalletDirectory 'isolated-mining-address.txt'
    if (Test-Path -LiteralPath $file) {
        if ([IO.File]::ReadAllText($file).Trim() -ne $address) { throw 'Wallet address changed unexpectedly' }
    } else {
        [IO.File]::WriteAllText($file, $address + [Environment]::NewLine)
    }
    Write-Output 'PASS: disposable wallet reopened offline and primary address saved privately'
    Write-Output ('Address file: '+$file)
} finally {
    if ($process -ne $null) { $process.Dispose() }
    if (Test-Path -LiteralPath $passfile) {
        [IO.File]::WriteAllBytes($passfile,(New-Object byte[] ([IO.File]::ReadAllBytes($passfile).Length)))
        Remove-Item -LiteralPath $passfile -Force
    }
    [Array]::Clear($plain,0,$plain.Length)
}
