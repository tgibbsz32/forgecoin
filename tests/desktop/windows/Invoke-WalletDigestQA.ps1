# Isolated native Windows wallet Digest verification — no user wallets.
# Never prints or stores seed phrases, personal credentials or live keys.
param(
  [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
  [string]$CandidateWallet = (Join-Path $env:USERPROFILE 'Downloads\ForgeCoin-Mainnet-20261026-Prelaunch-Wallet-v0.4\bin\forge-wallet-rpc.exe')
)
$ErrorActionPreference='Stop'
$manifest=Get-Content (Join-Path $RepositoryRoot 'docs\mainnet.identity.json') -Raw|ConvertFrom-Json
if($manifest.release_authorized -ne $false -or
   $manifest.pool.stratum_public -ne $false -or
   $manifest.pool.payouts_enabled -ne $false){throw 'Refusing QA: launch gate changed'}
$expected=$manifest.windows_prelaunch_binaries_sha256.'forge-wallet-rpc.exe'
if(!(Test-Path $CandidateWallet) -or
    (Get-FileHash $CandidateWallet -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected){
    throw 'Refusing unpinned native wallet binary'
}
$temporary=Join-Path $env:TEMP ('FRG-Private-Digest-QA-'+[Guid]::NewGuid().ToString('N'))
New-Item -Path $temporary -ItemType Directory|Out-Null
$wallets=Join-Path $temporary 'wallets'
New-Item -Path $wallets -ItemType Directory|Out-Null
$random=[byte[]]::new(32)
[Security.Cryptography.RandomNumberGenerator]::Fill($random)
$secret=([BitConverter]::ToString($random)).Replace('-','').ToLowerInvariant()
[Array]::Clear($random,0,$random.Length)
$user='frgqa'+[Guid]::NewGuid().ToString('N').Substring(0,12)
$cfg=Join-Path $temporary 'auth.conf'
[IO.File]::WriteAllText($cfg,('rpc-login='+$user+':'+$secret+[Environment]::NewLine))
$portListener=[System.Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0)
$portListener.Start()
$port=([Net.IPEndPoint]$portListener.LocalEndpoint).Port
$portListener.Stop()
$deadPort=49574
$p=$null
$env:FRG_QA_RPC_USER=$user
$env:FRG_QA_RPC_SECRET=$secret
try {
  $compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
  $testExe=Join-Path $temporary 'WalletRpcDigestProbe.exe'
  & $compiler /nologo /target:exe /reference:System.dll "/out:$testExe" `
     (Join-Path $RepositoryRoot 'apps\desktop\WalletRpcDigestTransport.cs') `
     (Join-Path $RepositoryRoot 'tests\desktop\windows\WalletRpcDigestProbe.cs')
  if($LASTEXITCODE -ne 0){throw 'Digest probe did not compile'}
  $args=@('--wallet-dir',('"'+$wallets+'"'), '--rpc-bind-ip','127.0.0.1',
      '--rpc-bind-port',([string]$port),'--daemon-address',('127.0.0.1:'+ $deadPort),
      '--config-file',('"'+$cfg+'"'),'--no-dns','--no-initial-sync',
      '--log-level','0', '--log-file',('"'+(Join-Path $temporary 'wallet.log')+'"'))
  $p=Start-Process -FilePath $CandidateWallet -ArgumentList $args -PassThru -NoNewWindow `
      -RedirectStandardOutput (Join-Path $temporary 'stdout.log') `
      -RedirectStandardError (Join-Path $temporary 'stderr.log')
  Start-Sleep -Seconds 4
  if($p.HasExited){throw 'Native wallet RPC failed to start'}
  & $testExe ([string]$port)
  if($LASTEXITCODE -ne 0){throw 'Native Windows wallet Digest acceptance failed'}
  Write-Output 'PASS: authenticated native wallet RPC rejects missing/wrong credentials and accepts correct credentials'
} finally {
  if($p -and !$p.HasExited){ Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
  Remove-Item Env:FRG_QA_RPC_USER -ErrorAction SilentlyContinue
  Remove-Item Env:FRG_QA_RPC_SECRET -ErrorAction SilentlyContinue
  $secret=$null
  Start-Sleep -Milliseconds 350
  Remove-Item $temporary -Recurse -Force -ErrorAction SilentlyContinue
}
