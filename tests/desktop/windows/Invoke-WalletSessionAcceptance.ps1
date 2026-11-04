# Native Windows FRG wallet RPC end-to-end authentication and recovery QA.
# No Oracle, daemon or mainnet mining; all wallets are disposable.
param(
 [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
 [string]$CandidateWallet = (Join-Path $env:USERPROFILE 'Downloads\ForgeCoin-Mainnet-20261026-Prelaunch-Wallet-v0.4\bin\forge-wallet-rpc.exe')
)
$ErrorActionPreference='Stop'
$manifest=Get-Content (Join-Path $RepositoryRoot 'docs\mainnet.identity.json') -Raw|ConvertFrom-Json
if($manifest.release_authorized -ne $false -or
   $manifest.pool.payouts_enabled -ne $false -or
   $manifest.pool.stratum_public -ne $false){throw 'Launch not locked; refusing native QA'}
$expected=$manifest.windows_prelaunch_binaries_sha256.'forge-wallet-rpc.exe'
if(!(Test-Path $CandidateWallet) -or
    (Get-FileHash $CandidateWallet -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected){
    throw 'Native wallet does not match checked-in SHA-256 candidate pin'
}
$folder=Join-Path $env:TEMP ('FRG-Session-Acceptance-'+[Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $folder|Out-Null
try{
  $compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
  $sources=Join-Path $RepositoryRoot 'apps\desktop'
  $qa=Join-Path $folder 'FRG-Wallet-RPC-Session-Acceptance.exe'
  & $compiler /nologo /target:exe /optimize+ "/out:$qa" `
    /reference:System.dll /reference:System.Web.Extensions.dll `
    (Join-Path $sources 'WalletRpcSession.cs') `
    (Join-Path $sources 'WalletRpcDigestTransport.cs') `
    (Join-Path $sources 'FrgWalletInput.cs') `
    (Join-Path $RepositoryRoot 'tests\desktop\windows\WalletRpcSessionAcceptance.cs')
  if($LASTEXITCODE -ne 0){throw 'Native wallet session test compilation failed'}
  & $qa $CandidateWallet
  if($LASTEXITCODE -ne 0){throw 'Native authenticated wallet create/restore/restart failed'}
  Write-Output 'PASS: native Windows private authenticated wallet integration accepted'
}finally{
  Remove-Item $folder -Recurse -Force -ErrorAction SilentlyContinue
}
