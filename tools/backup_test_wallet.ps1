# Encrypt a ForgeCoin test-wallet backup for the current Windows user.
# No actual credentials are bundled in this script. Output stays outside Git.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$WalletFile,
    [Parameter(Mandatory=$true)][string]$KeysFile,
    [Parameter(Mandatory=$true)][Security.SecureString]$RecoveryPhrase,
    [Parameter(Mandatory=$true)][Security.SecureString]$WalletPassword,
    [string]$BackupDirectory = (Join-Path $env:LOCALAPPDATA 'ForgeCoin\ProtectedWalletBackups')
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -eq 'Core' -and -not $IsWindows) {
    throw 'CurrentUser DPAPI backup requires Windows'
}
foreach ($inputFile in @($WalletFile, $KeysFile)) {
    if (-not (Test-Path -LiteralPath $inputFile -PathType Leaf)) {
        throw 'Both wallet cache and wallet keys file are required'
    }
}
$phrasePtr = [IntPtr]::Zero
$passwordPtr = [IntPtr]::Zero
try {
    $phrasePtr = [Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($RecoveryPhrase)
    $passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($WalletPassword)
    $record = @{
        format = 'ForgeCoin-local-DPAPI-v1'
        created_utc = [DateTime]::UtcNow.ToString('o')
        wallet_name = [IO.Path]::GetFileName($WalletFile)
        keys_name = [IO.Path]::GetFileName($KeysFile)
        wallet_base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($WalletFile))
        keys_base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($KeysFile))
        recovery_phrase = [Runtime.InteropServices.Marshal]::PtrToStringUni($phrasePtr)
        wallet_password = [Runtime.InteropServices.Marshal]::PtrToStringUni($passwordPtr)
    }
    $plaintext = [Text.Encoding]::UTF8.GetBytes(($record | ConvertTo-Json -Depth 4 -Compress))
    try {
        Add-Type -AssemblyName System.Security
        $ciphertext = [Security.Cryptography.ProtectedData]::Protect(
            $plaintext, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
    } finally {
        [Array]::Clear($plaintext, 0, $plaintext.Length)
    }
    [IO.Directory]::CreateDirectory($BackupDirectory) | Out-Null
    $name = 'frg-wallet-{0}-{1}.dpapi' -f ([DateTime]::UtcNow.ToString('yyyyMMddTHHmmss')),([guid]::NewGuid().ToString('N').Substring(0,8))
    $target = Join-Path $BackupDirectory $name
    $handle = [IO.File]::Open($target, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $handle.Write($ciphertext, 0, $ciphertext.Length)
        $handle.Flush($true)
    } finally {
        $handle.Dispose()
    }
    Write-Output ("Encrypted wallet backup created: {0}" -f $target)
    Write-Output 'Recovery is tied to this Windows user profile via DPAPI. Also maintain an independent offline recovery-phrase backup.'
} finally {
    if ($phrasePtr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeGlobalAllocUnicode($phrasePtr) }
    if ($passwordPtr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeGlobalAllocUnicode($passwordPtr) }
}
