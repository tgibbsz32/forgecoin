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
    $OutputRoot = Join-Path $ProjectRoot 'release\ForgeCoin-Desktop'
}

$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$BinRoot = Join-Path $OutputRoot 'bin'
$Compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'

if (-not (Test-Path -LiteralPath $Compiler)) {
    throw 'The .NET Framework C# compiler was not found.'
}

# Fail closed: MAINNET is still locked and public packaging is not approved.
# The repository identity file is a candidate specification, NOT a binary audit.
$IdentityPath = Join-Path $RepositoryRoot 'docs\mainnet.identity.json'
$Identity = Get-Content -LiteralPath $IdentityPath -Raw | ConvertFrom-Json
if ($Identity.release_authorized -ne $false -or
    $Identity.genesis_nonce -ne 20261026 -or
    $Identity.genesis_hash -cne '4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c' -or
    $Identity.network_uuid -cne 'bd936359-09e4-4fdb-8ec0-12fa9d6ef090' -or
    $Identity.ports.p2p -ne 39480 -or
    $Identity.ports.daemon_rpc -ne 39481 -or
    $Identity.ports.zmq_rpc -ne 39482 -or
    $Identity.address_prefixes.standard -ne 190 -or
    $Identity.pool.payouts_enabled -ne $false -or
    $Identity.pool.stratum_public -ne $false) {
    throw 'Refusing desktop build: frozen prelaunch identity or release lock changed.'
}

if ($SourceOnly) {
    if ($PrivatePrelaunch -or $ForgeBin -or $XmrigRoot) {
        throw 'Source-only compile must not accept native sidecars or mining binaries.'
    }
} else {
    if (-not $PrivatePrelaunch) {
        throw 'Public desktop package is NOT authorized. Use -SourceOnly or explicit -PrivatePrelaunch for offline testing.'
    }
    if ([string]::IsNullOrWhiteSpace($ForgeBin)) {
        throw 'Explicit -ForgeBin directory required for private prelaunch packaging.'
    }
    if ($XmrigRoot) {
        throw 'XMRig bundling is blocked pending independently reviewed binary provenance and licensing.'
    }
    $ForgeBin = (Resolve-Path -LiteralPath $ForgeBin).Path
    @('forged.exe', 'forge-wallet-rpc.exe') | ForEach-Object {
        $candidate = Join-Path $ForgeBin $_
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            throw "Missing required ForgeCoin binary: $_"
        }
        $reviewedHash = $Identity.windows_prelaunch_binaries_sha256.$_
        if (-not ($reviewedHash -is [string]) -or
            $reviewedHash -notmatch '^[a-f0-9]{64}

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
    Write-Host 'PASS: Windows Forms source compiled. NO daemon, wallet, miner or release package created.'
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
Mainnet activation is NOT approved. No mining, wallet transfers, public Stratum,
pool payouts or public distribution are authorized by this build.
The bundled daemon and wallet RPC matched repository-listed SHA-256 pins,
but independent binary provenance, current frozen consensus, native payout,
installer QA and release signing are NOT certified by this check.
'@ | Set-Content -LiteralPath (Join-Path $OutputRoot 'PRIVATE-PRELAUNCH-NOT-FOR-DISTRIBUTION.txt') -Encoding ASCII
Write-Host "Private prelaunch package created (NOT a public release): $OutputRoot"
) {
            throw "Missing reviewed candidate SHA-256 pin: $_"
        }
        $foundHash = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash
        if ($foundHash -ine $reviewedHash) {
            throw "Native sidecar SHA-256 mismatch for $_. NEVER substitute retired-chain binaries."
        }
    }
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw 'Output directory already exists. Choose a new -OutputRoot to preserve existing files.'
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
Write-Host "Built $OutputRoot"
