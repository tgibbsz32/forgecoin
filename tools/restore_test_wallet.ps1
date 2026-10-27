# Restore encrypted ForgeCoin wallet files on the same Windows user account.
# Recovery phrase/password remain inside the encrypted archive; they are not
# displayed, logged, or written as plaintext by this command.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$BackupPath,
    [Parameter(Mandatory=$true)][string]$DestinationDirectory
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -eq 'Core' -and -not $IsWindows) {
    throw 'Windows CurrentUser DPAPI is required'
}
if (-not (Test-Path -LiteralPath $BackupPath -PathType Leaf)) {
    throw 'Encrypted backup not found'
}
Add-Type -AssemblyName System.Security
$cipher = [IO.File]::ReadAllBytes($BackupPath)
if ($cipher.Length -lt 64 -or $cipher.Length -gt 50MB) {
    throw 'Invalid encrypted backup size'
}
$plain = [Security.Cryptography.ProtectedData]::Unprotect(
    $cipher, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
try {
    $record = [Text.Encoding]::UTF8.GetString($plain) | ConvertFrom-Json
    if ($record.format -ne 'ForgeCoin-local-DPAPI-v1') {
        throw 'Unexpected backup format'
    }
    foreach ($field in @('wallet_name','keys_name','wallet_base64','keys_base64','recovery_phrase','wallet_password')) {
        if ($null -eq $record.$field) { throw 'Incomplete encrypted wallet backup' }
    }
    foreach ($name in @($record.wallet_name, $record.keys_name)) {
        if ([IO.Path]::GetFileName($name) -cne $name -or
            [string]::IsNullOrWhiteSpace($name) -or $name.Contains('..')) {
            throw 'Invalid wallet file name in encrypted backup'
        }
    }
    if ($record.wallet_name -eq $record.keys_name) {
        throw 'Wallet files must be distinct'
    }
    [IO.Directory]::CreateDirectory($DestinationDirectory) | Out-Null
    $walletPath = Join-Path $DestinationDirectory $record.wallet_name
    $keysPath = Join-Path $DestinationDirectory $record.keys_name
    foreach ($path in @($walletPath, $keysPath)) {
        if (Test-Path -LiteralPath $path) { throw 'Destination already contains wallet file; refusing overwrite' }
    }
    $written = @()
    try {
        foreach ($pair in @(@($walletPath, $record.wallet_base64), @($keysPath, $record.keys_base64))) {
            $bytes = [Convert]::FromBase64String($pair[1])
            $file = [IO.File]::Open($pair[0], [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
            try { $file.Write($bytes, 0, $bytes.Length); $file.Flush($true) }
            finally { $file.Dispose(); [Array]::Clear($bytes, 0, $bytes.Length) }
            $written += $pair[0]
        }
    } catch {
        foreach ($path in $written) { Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue }
        throw
    }
    Write-Output 'Restored encrypted-backup wallet files to the requested directory; existing files were not overwritten.'
    Write-Output 'The recovery phrase and password remain protected in the DPAPI archive.'
} finally {
    [Array]::Clear($plain, 0, $plain.Length)
}
