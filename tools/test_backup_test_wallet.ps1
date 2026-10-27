# Automated test with dummy credentials ONLY. Never use an actual seed here.
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:TEMP ('frg-vault-test-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($root) | Out-Null
try {
    $wallet = Join-Path $root 'dummy-wallet'
    $keys = Join-Path $root 'dummy-wallet.keys'
    [IO.File]::WriteAllBytes($wallet, [byte[]](1,3,5,7))
    [IO.File]::WriteAllBytes($keys, [byte[]](2,4,6,8))
    $phrase = ConvertTo-SecureString 'dummy-only-test-recovery-phrase' -AsPlainText -Force
    $password = ConvertTo-SecureString 'dummy-only-test-password' -AsPlainText -Force
    $backupDir = Join-Path $root 'backups'
    $out = & (Join-Path $PSScriptRoot 'backup_test_wallet.ps1') `
        -WalletFile $wallet -KeysFile $keys -RecoveryPhrase $phrase `
        -WalletPassword $password -BackupDirectory $backupDir
    $backup = @(Get-ChildItem -LiteralPath $backupDir -Filter '*.dpapi' -File)
    if ($backup.Count -ne 1) { throw 'Expected exactly one encrypted backup' }
    $cipher = [IO.File]::ReadAllBytes($backup[0].FullName)
    $raw = [Text.Encoding]::UTF8.GetString($cipher)
    if ($raw.Contains('dummy-only-test')) { throw 'Plaintext credentials found on disk' }
    Add-Type -AssemblyName System.Security
    $plain = [Security.Cryptography.ProtectedData]::Unprotect(
        $cipher, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
    try {
        $record = [Text.Encoding]::UTF8.GetString($plain) | ConvertFrom-Json
        if ($record.recovery_phrase -ne 'dummy-only-test-recovery-phrase' -or
            $record.wallet_password -ne 'dummy-only-test-password' -or
            $record.wallet_base64 -ne [Convert]::ToBase64String([byte[]](1,3,5,7)) -or
            $record.keys_base64 -ne [Convert]::ToBase64String([byte[]](2,4,6,8))) {
            throw 'Backup content did not round-trip'
        }
    } finally {
        [Array]::Clear($plain, 0, $plain.Length)
    }
    $restored = Join-Path $root 'restored'
    & (Join-Path $PSScriptRoot 'restore_test_wallet.ps1') -BackupPath $backup[0].FullName -DestinationDirectory $restored | Out-Null
    if ([Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $restored 'dummy-wallet'))) -ne
        [Convert]::ToBase64String([byte[]](1,3,5,7)) -or
        [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $restored 'dummy-wallet.keys'))) -ne
        [Convert]::ToBase64String([byte[]](2,4,6,8))) { throw 'Restored file mismatch' }
    $blocked = $false
    try {
        & (Join-Path $PSScriptRoot 'restore_test_wallet.ps1') -BackupPath $backup[0].FullName -DestinationDirectory $restored | Out-Null
    } catch { $blocked = $true }
    if (-not $blocked) { throw 'Restore unexpectedly overwrote existing wallet' }
    Write-Output 'PASS: dummy encrypted wallet backup, restoration and overwrite protection'
} finally {
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
