# ForgeCoin isolated-test wallet only: never use for production funds.
# Generate offline, capture the seed in process memory, and encrypt both wallet
# files, mnemonic and a generated password with current-user Windows DPAPI.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$WalletExecutable,
    [string]$ParentDirectory = (Join-Path $env:LOCALAPPDATA 'ForgeCoin\DisposableTestWallets')
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([IO.Path]::GetFileName($WalletExecutable) -ne 'forge-wallet-cli.exe' -or
    -not (Test-Path -LiteralPath $WalletExecutable -PathType Leaf)) {
    throw 'An explicit source-matched forge-wallet-cli.exe is required'
}
$root = Join-Path $ParentDirectory ('legacy-prefix90-'+[guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($root) | Out-Null
$wallet = Join-Path $root 'isolated-test-wallet'
$passwordFile = Join-Path $root '.temporary-wallet-password'
$random = New-Object byte[] 48
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($random)
$rng.Dispose()
$password = [Convert]::ToBase64String($random)
[Array]::Clear($random,0,$random.Length)
$seed = $null
$process = $null
$backedUp = $false
try {
    [IO.File]::WriteAllText($passwordFile,$password,[Text.Encoding]::ASCII)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = [IO.Path]::GetFullPath($WalletExecutable)
    $psi.WorkingDirectory = $root
    $psi.Arguments = '--offline --generate-new-wallet "'+$wallet+'" --password-file "'+$passwordFile+'" --mnemonic-language English --log-file NUL --command seed'
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.EnvironmentVariables['PATH'] = ('C:\msys64\mingw64\bin;' + $env:PATH)
    $process = [Diagnostics.Process]::Start($psi)
    $outputTask = $process.StandardOutput.ReadToEndAsync()
    $errorTask = $process.StandardError.ReadToEndAsync()
    for ($i=0;$i -lt 10;$i++) { $process.StandardInput.WriteLine('') }
    $process.StandardInput.Close()
    if (-not $process.WaitForExit(45000)) {
        $process.Kill()
        $process.WaitForExit()
        throw 'Offline wallet CLI did not finish within timeout'
    }
    $output = $outputTask.GetAwaiter().GetResult()
    $null = $errorTask.GetAwaiter().GetResult()
    if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $wallet) -or
        -not (Test-Path -LiteralPath ($wallet+'.keys'))) {
        throw 'Offline wallet generation did not produce both wallet files'
    }
    # Match a complete Monero-derived 25-word mnemonic (not a log excerpt).
    $matches = [regex]::Matches($output, '(?m)^\s*([a-z]{2,24}(?:\s+[a-z]{2,24}){24})\s*$')
    if ($matches.Count -ne 1) {
        throw 'Mnemonic could not be unambiguously extracted; wallet will be discarded'
    }
    $seed = $matches[0].Groups[1].Value -replace '\s+',' '
    $protectedSeed = ConvertTo-SecureString $seed -AsPlainText -Force
    $protectedPassword = ConvertTo-SecureString $password -AsPlainText -Force
    $backupMessages = & (Join-Path $PSScriptRoot 'backup_test_wallet.ps1') `
        -WalletFile $wallet -KeysFile ($wallet+'.keys') `
        -RecoveryPhrase $protectedSeed -WalletPassword $protectedPassword
    $backedUp = $true
    Write-Output 'PASS: disposable offline wallet generated and DPAPI backup saved outside Git'
    foreach ($m in $backupMessages) { if ($m -like 'Encrypted wallet backup created:*') { Write-Output $m } }
    Write-Output ('Wallet files: '+$root)
} finally {
    if ($process -ne $null) { $process.Dispose() }
    # Test-only password file: best-effort in-place overwrite before deletion.
    if (Test-Path -LiteralPath $passwordFile) {
        [IO.File]::WriteAllBytes($passwordFile,(New-Object byte[] ([Text.Encoding]::ASCII.GetByteCount($password))))
        Remove-Item -LiteralPath $passwordFile -Force
    }
    $password = $null
    $seed = $null
    if (-not $backedUp) {
        Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
    }
}
