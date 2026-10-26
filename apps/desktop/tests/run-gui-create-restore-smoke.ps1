[CmdletBinding()]
param(
    [string]$Bundle = (Join-Path $env:USERPROFILE 'Downloads\ForgeCoin-Mainnet-20261026-Prelaunch-Wallet-v0.3'),
    [string]$GenesisData = (Join-Path $env:TEMP 'forgecoin-mainnet-20261026-genesis-readonly-evidence')
)
$ErrorActionPreference='Stop'
$bundle=(Resolve-Path -LiteralPath $Bundle).Path
$bin=Join-Path $bundle 'bin'
$genesisData=(Resolve-Path -LiteralPath $GenesisData).Path
$csc='C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$harness=Join-Path $bundle 'ForgeCoin-Gui-Wallet-Create-Restore-Smoke-20261026.exe'
$prefix='ui-smoke-20261026-'+([guid]::NewGuid().ToString('N').Substring(0,12))
$walletdir=Join-Path $env:LOCALAPPDATA 'ForgeCoin\wallets-mainnet-20261026'
$node=$null
if(!(Test-Path (Join-Path $genesisData 'genesis-evidence.json'))){throw 'Offline genesis-only evidence missing'}
if(Get-NetTCPConnection -LocalPort 39481,39483 -State Listen -ErrorAction SilentlyContinue){throw 'RPC port already in use; refusing to interact with existing service'}
& $csc /nologo /target:exe /optimize+ /platform:anycpu /reference:System.dll /reference:System.Core.dll /reference:System.Drawing.dll "/out:$harness" (Join-Path $PSScriptRoot 'GuiCreateRestoreSmoke.cs')
if($LASTEXITCODE -ne 0){throw 'GUI integration harness does not compile'}
$env:Path='C:\Windows\System32;C:\Windows'
try {
  $args=@('--data-dir',$genesisData,'--offline','--p2p-bind-ip','127.0.0.1','--p2p-bind-port','49580','--rpc-bind-ip','127.0.0.1','--rpc-bind-port','39481','--no-zmq','--no-igd','--disable-dns-checkpoints','--check-updates','disabled','--non-interactive','--log-level','0')
  $node=Start-Process -FilePath (Join-Path $bin 'forged.exe') -ArgumentList $args -WorkingDirectory $bin -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $env:TEMP 'ForgeCoin-Gui-Smoke-Offline-Node.out') -RedirectStandardError (Join-Path $env:TEMP 'ForgeCoin-Gui-Smoke-Offline-Node.err')
  $ready=$false
  for($i=0;$i -lt 40;$i++){
    $node.Refresh()
    if($node.HasExited){throw ('Offline node exited '+$node.ExitCode)}
    try {
      $info=Invoke-RestMethod -Uri 'http://127.0.0.1:39481/get_info' -TimeoutSec 2
      if([int]$info.height -eq 1 -and $info.nettype -eq 'mainnet'){$ready=$true;break}
    }catch{}
    Start-Sleep -Milliseconds 400
  }
  if(-not $ready){throw 'Genesis-only daemon did not start'}
  $payload=@{jsonrpc='2.0';id='guismoke';method='get_block_header_by_height';params=@{height=0}}|ConvertTo-Json -Compress
  $header=(Invoke-RestMethod -Uri 'http://127.0.0.1:39481/json_rpc' -Method Post -Body $payload -ContentType 'application/json' -TimeoutSec 4).result.block_header
  if($header.nonce -ne 20261026 -or $header.hash -ne '4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c'){throw 'Wrong chain identity, refuse GUI test'}
  Write-Output 'OFFLINE_GENESIS_ONLY_AND_HASH_VERIFIED'
  $qaArgs='"' + (Join-Path $bundle 'ForgeCoin Desktop.exe') + '" ' + $prefix
  $qaOut=Join-Path $env:TEMP 'ForgeCoin-Gui-Smoke-Harness.out'
  $qaErr=Join-Path $env:TEMP 'ForgeCoin-Gui-Smoke-Harness.err'
  $qa=Start-Process -FilePath $harness -ArgumentList $qaArgs -WorkingDirectory $bundle -PassThru -RedirectStandardOutput $qaOut -RedirectStandardError $qaErr
  if(-not $qa.WaitForExit(75000)){
    Stop-Process -Id $qa.Id -Force -ErrorAction SilentlyContinue
    throw 'GUI integration test exceeded 75 seconds; forced cleanup of disposable test process'
  }
  $qa.Refresh()
  $qaOutput=Get-Content $qaOut -ErrorAction SilentlyContinue
  $qaOutput | Select-Object -First 15
  if($qa.ExitCode -is [int] -and $qa.ExitCode -ne 0){
    Get-Content $qaErr -ErrorAction SilentlyContinue | Select-Object -First 12
    throw ('REAL_GUI_CREATE_RESTORE_TEST_EXIT='+$qa.ExitCode)
  }
  if(-not ($qaOutput | Where-Object {$_ -eq 'PASS GUI wallet lifecycle create, backup dialog, close, restore, compare and close'})){
    throw 'GUI integration test did not report completed lifecycle'
  }
  $after=Invoke-RestMethod -Uri 'http://127.0.0.1:39481/get_info' -TimeoutSec 3
  if([int]$after.height -ne 1){throw 'Mainnet was mined by test, fail'}
  Write-Output 'MAINNET_GENESIS_HEIGHT_UNCHANGED'
} finally {
  if($node){
    try{$q=@{jsonrpc='2.0';id='guismoke-stop';method='stop_daemon';params=@{}}|ConvertTo-Json -Compress
        Invoke-RestMethod -Uri 'http://127.0.0.1:39481/json_rpc' -Method Post -ContentType 'application/json' -Body $q -TimeoutSec 3|Out-Null}catch{}
    Start-Sleep -Milliseconds 400
    try{$node.Refresh();if(-not $node.HasExited){Stop-Process -Id $node.Id -Force}}catch{}
  }
  $files=@(Get-ChildItem $walletdir -File -ErrorAction SilentlyContinue | Where-Object { $_.Name.StartsWith($prefix, [StringComparison]::Ordinal) })
  foreach($file in $files){Remove-Item -LiteralPath $file.FullName -Force -ErrorAction Stop}
  Write-Output ('DISPOSABLE_SYNTHETIC_WALLET_FILES_DELETED='+$files.Count)
  if(Test-Path $harness){Remove-Item -LiteralPath $harness -Force -ErrorAction SilentlyContinue}
  Write-Output 'OWNER_TREASURY_WALLET_NOT_TOUCHED'
}
