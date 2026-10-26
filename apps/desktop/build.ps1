[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ForgeBin,

    [string]$MingwBin = 'C:\msys64\mingw64\bin',
    [string]$XmrigRoot,
    [string]$OutputRoot
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepositoryRoot = (Resolve-Path (Join-Path $ProjectRoot '..\..')).Path

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $ProjectRoot 'release\ForgeCoin-Desktop'
}

$ForgeBin = (Resolve-Path -LiteralPath $ForgeBin).Path
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$BinRoot = Join-Path $OutputRoot 'bin'
$Compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'

if (-not (Test-Path -LiteralPath $Compiler)) {
    throw 'The .NET Framework C# compiler was not found.'
}

@('forged.exe', 'forge-wallet-rpc.exe', 'forge-wallet-cli.exe') | ForEach-Object {
    if (-not (Test-Path -LiteralPath (Join-Path $ForgeBin $_))) {
        throw "Missing required ForgeCoin binary: $_"
    }
}

# Packaging old-chain binaries as the new mainnet would be a fund-loss risk.
# Pin EVERY native executable to the genesis-frozen test-built hashes.
$IdentityFile = Join-Path $RepositoryRoot 'config\mainnet.identity.json'
if (-not (Test-Path -LiteralPath $IdentityFile)) {
    throw 'New-mainnet release identity manifest missing.'
}
$Identity = Get-Content -LiteralPath $IdentityFile -Raw | ConvertFrom-Json
if ($null -ne $Identity.consensus_guard_stage) {
    throw 'Consensus guard changes require reviewed native rebuilds; packaging is blocked.'
}
if ($Identity.genesis_nonce -ne 20261026 -or
    $Identity.stage -ne 'genesis-frozen' -or
    [string]::IsNullOrWhiteSpace($Identity.genesis_hash) -or
    $Identity.release_authorized -ne $false) {
    throw 'Refusing packaging: expected locked new-mainnet genesis and PRELAUNCH status.'
}
foreach ($Name in @('forged.exe', 'forge-wallet-rpc.exe', 'forge-wallet-cli.exe')) {
    $Expected = $Identity.windows_prelaunch_binaries_sha256.PSObject.Properties[$Name].Value
    if ([string]::IsNullOrWhiteSpace($Expected)) {
        throw "No pinned new-mainnet hash for $Name"
    }
    $Actual = (Get-FileHash -LiteralPath (Join-Path $ForgeBin $Name) -Algorithm SHA256).Hash
    if ($Actual -ine $Expected) {
        throw "Wrong network, stale build or tampered executable: $Name"
    }
}

if (Test-Path -LiteralPath $OutputRoot) {
    throw "Output directory already exists. Choose a new -OutputRoot to preserve existing files."
}
New-Item -ItemType Directory -Path $BinRoot -Force | Out-Null

& $Compiler /nologo /target:winexe /optimize+ /platform:anycpu `
    /win32manifest:"$ProjectRoot\app.manifest" `
    /out:"$OutputRoot\ForgeCoin Desktop.exe" `
    /reference:System.dll /reference:System.Core.dll /reference:System.Drawing.dll `
    /reference:System.Windows.Forms.dll /reference:System.Web.Extensions.dll `
    "$ProjectRoot\Program.cs"
if ($LASTEXITCODE -ne 0) {
    throw "C# compilation failed with exit code $LASTEXITCODE"
}

Copy-Item -LiteralPath (Join-Path $ForgeBin 'forged.exe') -Destination $BinRoot
Copy-Item -LiteralPath (Join-Path $ForgeBin 'forge-wallet-rpc.exe') -Destination $BinRoot
Copy-Item -LiteralPath (Join-Path $ForgeBin 'forge-wallet-cli.exe') -Destination $BinRoot

$RuntimeDlls = @(
    'libiconv-2.dll', 'libicuin78.dll', 'libicuuc78.dll', 'libicudt78.dll',
    'libgcc_s_seh-1.dll', 'libstdc++-6.dll', 'libwinpthread-1.dll'
)
foreach ($Dll in $RuntimeDlls) {
    $DllPath = Join-Path $MingwBin $Dll
    if (-not (Test-Path -LiteralPath $DllPath)) {
        throw "Missing MinGW runtime file: $DllPath"
    }
    Copy-Item -LiteralPath $DllPath -Destination $BinRoot
}

if (-not [string]::IsNullOrWhiteSpace($XmrigRoot)) {
    $XmrigRoot = (Resolve-Path -LiteralPath $XmrigRoot).Path
    $XmrigBin = Join-Path $BinRoot 'xmrig'
    New-Item -ItemType Directory -Path $XmrigBin -Force | Out-Null
    @('xmrig.exe', 'LICENSE') | ForEach-Object {
        $SourcePath = Join-Path $XmrigRoot $_
        if (-not (Test-Path -LiteralPath $SourcePath)) {
            throw "Missing XMRig file: $SourcePath"
        }
    }
    Copy-Item -LiteralPath (Join-Path $XmrigRoot 'xmrig.exe') -Destination $XmrigBin
    Copy-Item -LiteralPath (Join-Path $XmrigRoot 'LICENSE') -Destination (Join-Path $XmrigBin 'LICENSE-XMRIG')
    $DriverPath = Join-Path $XmrigRoot 'WinRing0x64.sys'
    if (Test-Path -LiteralPath $DriverPath) {
        Copy-Item -LiteralPath $DriverPath -Destination $XmrigBin
    }
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'XMRIG-NOTICE.txt') -Destination $XmrigBin
}

@('README.txt', 'INSTALL.md', 'VALIDATION.md', 'TREASURY-WALLET.md') | ForEach-Object {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot $_) -Destination $OutputRoot
}
Copy-Item -LiteralPath (Join-Path $RepositoryRoot 'LICENSE') -Destination $OutputRoot
Copy-Item -LiteralPath $IdentityFile -Destination (Join-Path $OutputRoot 'mainnet.identity.json')
Write-Host 'PRELAUNCH WALLET KIT ONLY: solo and pool mining remain disabled until mainnet launch authorization.'

Write-Host "Built $OutputRoot"
