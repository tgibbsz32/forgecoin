[CmdletBinding()]
param(
    [string]$ForgeBin,
    [switch]$SourceOnly,
    [switch]$PrivatePrelaunch,

    [string]$MingwBin = 'C:\msys64\mingw64\bin',
    [string]$XmrigRoot,
    [string]$OutputRoot
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepositoryRoot = (Resolve-Path (Join-Path $ProjectRoot '..\..')).Path

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    if ($SourceOnly) {
        $OutputRoot = Join-Path $ProjectRoot 'qa-build\ForgeCoin-Desktop-SourceOnly'
    } else {
        $OutputRoot = Join-Path $ProjectRoot 'release\ForgeCoin-Desktop'
    }
}

$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$BinRoot = Join-Path $OutputRoot 'bin'
$Compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'

if (-not (Test-Path -LiteralPath $Compiler)) {
    throw 'The .NET Framework C# compiler was not found.'
}

# The identity file describes a frozen, unlaunched chain; it does NOT certify binaries.
$Identity = Get-Content -LiteralPath (Join-Path $RepositoryRoot 'docs\mainnet.identity.json') -Raw | ConvertFrom-Json
if ($Identity.release_authorized -ne $false -or
    $Identity.genesis_nonce -ne 20261026 -or
    $Identity.genesis_hash -cne '4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c' -or
    $Identity.network_uuid -cne 'bd936359-09e4-4fdb-8ec0-12fa9d6ef090' -or
    $Identity.ports.p2p -ne 39480 -or $Identity.ports.daemon_rpc -ne 39481 -or
    $Identity.ports.zmq_rpc -ne 39482 -or
    $Identity.address_prefixes.standard -ne 190 -or
    $Identity.address_prefixes.integrated -ne 191 -or
    $Identity.address_prefixes.subaddress -ne 192 -or
    $Identity.pool.payouts_enabled -ne $false -or
    $Identity.pool.stratum_public -ne $false) {
    throw 'Refusing desktop build: frozen prelaunch identity or release lock changed.'
}
if ($SourceOnly) {
    if ($PrivatePrelaunch -or $ForgeBin -or $XmrigRoot) {
        throw 'Source-only compile does not accept sidecars or mining binaries.'
    }
} else {
    if (-not $PrivatePrelaunch) {
        throw 'Public packaging NOT authorized. Only -SourceOnly or explicit -PrivatePrelaunch offline QA is allowed.'
    }
    if ([string]::IsNullOrWhiteSpace($ForgeBin)) {
        throw 'Explicit -ForgeBin path required for private prelaunch packaging.'
    }
    if ($XmrigRoot) {
        throw 'Bundled XMRig is blocked pending independent binary provenance and licensing review.'
    }
    $ForgeBin = (Resolve-Path -LiteralPath $ForgeBin).Path
    @('forged.exe', 'forge-wallet-rpc.exe') | ForEach-Object {
        $candidate = Join-Path $ForgeBin $_
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            throw "Missing native FRG sidecar: $_"
        }
        $expected = $Identity.windows_prelaunch_binaries_sha256.$_
        if (-not ($expected -is [string]) -or $expected -notmatch '^[a-f0-9]{64}$') {
            throw "Missing reviewed candidate hash pin for $_"
        }
        $actual = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash
        if ($actual -ine $expected) {
            throw "Native FRG sidecar hash mismatch for $_. Retired or unreviewed binaries forbidden."
        }
    }
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw 'Output directory already exists. Choose a fresh -OutputRoot to preserve prior files.'
}
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

& $Compiler /nologo /target:winexe /optimize+ /platform:anycpu `
    /win32manifest:"$ProjectRoot\app.manifest" `
    /out:"$OutputRoot\ForgeCoin Desktop.exe" `
    /reference:System.dll /reference:System.Core.dll /reference:System.Drawing.dll `
    /reference:System.Windows.Forms.dll /reference:System.Web.Extensions.dll `
    "$ProjectRoot\Program.cs" "$ProjectRoot\SolanaWallet.cs" "$ProjectRoot\SolanaVault.cs"
if ($LASTEXITCODE -ne 0) {
    throw "C# compilation failed with exit code $LASTEXITCODE"
}

if ($SourceOnly) {
    Write-Host 'PASS: Windows Forms SOURCE ONLY compiled. No daemon, wallet, miner or distributable created.'
    return
}
New-Item -ItemType Directory -Path $BinRoot -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $ForgeBin 'forged.exe') -Destination $BinRoot
Copy-Item -LiteralPath (Join-Path $ForgeBin 'forge-wallet-rpc.exe') -Destination $BinRoot

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

@('README.txt', 'INSTALL.md', 'VALIDATION.md') | ForEach-Object {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot $_) -Destination $OutputRoot
}
Copy-Item -LiteralPath (Join-Path $RepositoryRoot 'LICENSE') -Destination $OutputRoot

$LogoPath = Join-Path $RepositoryRoot "docs\images\forgecoin-logo.png"
if (Test-Path -LiteralPath $LogoPath) {
    Copy-Item -LiteralPath $LogoPath -Destination (Join-Path $OutputRoot "forgecoin-logo.png")
}
@'
PRIVATE PRELAUNCH TEST-ONLY PACKAGE
No mainnet mining, native wallet payouts, public Stratum or public distribution
is authorized. Sidecar SHA-256 pins matched this repository identity reference
but this is NOT independent provenance, reviewed consensus or signing proof.
'@ | Set-Content -LiteralPath (Join-Path $OutputRoot 'PRIVATE-PRELAUNCH-NOT-FOR-DISTRIBUTION.txt') -Encoding ASCII
Write-Host "Built PRIVATE PRELAUNCH ONLY (not a public release): $OutputRoot"
