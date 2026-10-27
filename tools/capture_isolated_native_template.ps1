# Temporary loopback-only ForgeCoin daemon capture. No mining/payouts/peers.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$DaemonExecutable,
    [Parameter(Mandatory=$true)][string]$ExpectedSha256,
    [Parameter(Mandatory=$true)][string]$AddressFile,
    [switch]$SubmitUnmodifiedBlock,
    [switch]$SubmitModifiedNonceBlock,
    [switch]$SubmitModifiedReservedBlock,
    [ValidateRange(1024,65532)][int]$PortBase = 49580,
    [string]$BaseDirectory = (Join-Path $env:LOCALAPPDATA 'ForgeCoin\IsolatedTemplateCaptures')
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (($SubmitUnmodifiedBlock -and ($SubmitModifiedNonceBlock -or $SubmitModifiedReservedBlock)) -or
    ($SubmitModifiedNonceBlock -and $SubmitModifiedReservedBlock)) {
    throw 'Select exactly one isolated candidate submission mode'
}
if ([IO.Path]::GetFileName($DaemonExecutable) -ne 'forged.exe') {
    throw 'Expected source-matched forged.exe'
}
if ((Get-FileHash -LiteralPath $DaemonExecutable -Algorithm SHA256).Hash -ne $ExpectedSha256.ToUpperInvariant()) {
    throw 'Daemon checksum mismatch'
}
$occupied = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in @($PortBase,($PortBase+1),($PortBase+2)) })
if ($occupied.Count -gt 0) { throw 'Isolated test port already in use; refusing to contact an existing process' }
$address = [IO.File]::ReadAllText($AddressFile).Trim()
if ($address -notmatch '^[1-9A-HJ-NP-Za-km-z]{95}$') {
    throw 'Invalid disposable wallet address'
}
$root = Join-Path $BaseDirectory ([guid]::NewGuid().ToString('N'))
$dataDir = Join-Path $root 'chain'
[IO.Directory]::CreateDirectory($dataDir) | Out-Null
$stdoutFile = Join-Path $root 'daemon.stdout.log'
$stderrFile = Join-Path $root 'daemon.stderr.log'
$captureFile = Join-Path $root 'native-template.json'
$process = $null
$rpc = 'http://127.0.0.1:'+($PortBase+1)+'/json_rpc'
try {
    $psi = New-Object Diagnostics.ProcessStartInfo
    $psi.FileName = [IO.Path]::GetFullPath($DaemonExecutable)
    $psi.WorkingDirectory = $root
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.EnvironmentVariables['PATH'] = ('C:\msys64\mingw64\bin;' + $env:PATH)
    $psi.Arguments = ('--offline --no-igd --data-dir "'+$dataDir+
        '" --rpc-bind-ip 127.0.0.1 --rpc-bind-port '+($PortBase+1)+
        ' --p2p-bind-ip 127.0.0.1 --p2p-bind-port '+$PortBase+
        ' --zmq-rpc-bind-ip 127.0.0.1 --zmq-rpc-bind-port '+($PortBase+2)+
        ' --log-file "'+(Join-Path $root 'daemon.log')+'"')
    $process = [Diagnostics.Process]::Start($psi)
    $outTask = $process.StandardOutput.ReadToEndAsync()
    $errTask = $process.StandardError.ReadToEndAsync()
    $info = $null
    for ($i=0;$i -lt 90;$i++) {
        if ($process.HasExited) { throw 'Isolated ForgeCoin daemon exited during startup' }
        try {
            $payload = @{ jsonrpc='2.0';id='probe';method='get_info' } | ConvertTo-Json -Compress
            $info = Invoke-RestMethod -Uri $rpc -Method Post -Body $payload -ContentType 'application/json' -TimeoutSec 2
            if ($info.result) { break }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    if (-not $info -or -not $info.result) { throw 'Isolated daemon RPC not ready' }
    $req = @{ jsonrpc='2.0';id='isolated-capture';method='get_block_template';
              params=@{wallet_address=$address;reserve_size=8} } | ConvertTo-Json -Depth 5 -Compress
    $capture = Invoke-RestMethod -Uri $rpc -Method Post -Body $req -ContentType 'application/json' -TimeoutSec 15
    if (-not $capture.result -or -not $capture.result.blocktemplate_blob -or
        -not $capture.result.blockhashing_blob) {
        throw 'Native daemon did not return both template blobs'
    }
    [IO.File]::WriteAllText($captureFile,($capture | ConvertTo-Json -Depth 8 -Compress),
        (New-Object Text.UTF8Encoding($false)))
    if ($SubmitUnmodifiedBlock -or $SubmitModifiedNonceBlock -or $SubmitModifiedReservedBlock) {
        # This tests only isolated daemon block acceptance.
        # It is NOT a miner-discovered block or Stratum pool submission.
        if ([int64]$capture.result.difficulty -ne 1 -or [int64]$capture.result.height -ne 1) {
            throw 'Block acceptance test requires isolated height 1 and difficulty 1'
        }
        $candidateBlob = $capture.result.blocktemplate_blob
        if ($SubmitModifiedNonceBlock -or $SubmitModifiedReservedBlock) {
            $reservedMode = [bool]$SubmitModifiedReservedBlock
            $candidatePath = Join-Path $root $(if ($reservedMode) {
                'reserved-modified-candidate.json'
            } else {
                'nonce-modified-candidate.json'
            })
            $module = if ($reservedMode) {
                'tools.build_isolated_reserved_candidate'
            } else {
                'tools.build_isolated_nonce_candidate'
            }
            $helper = New-Object Diagnostics.ProcessStartInfo
            $helper.FileName = (Get-Command py.exe -ErrorAction Stop).Source
            $helper.WorkingDirectory = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
            $helper.UseShellExecute = $false
            $helper.CreateNoWindow = $true
            $helper.Arguments = ('-m '+$module+' --capture "'+
                $captureFile+'" --output "'+$candidatePath+'" --nonce 01020304')
            $helperProcess = [Diagnostics.Process]::Start($helper)
            try {
                if (-not $helperProcess.WaitForExit(20000)) {
                    $helperProcess.Kill()
                    $helperProcess.WaitForExit()
                    throw 'Offline candidate generation timed out'
                }
                if ($helperProcess.ExitCode -ne 0) {
                    throw 'Offline candidate builder failed'
                }
            } finally { $helperProcess.Dispose() }
            $candidate = Get-Content -LiteralPath $candidatePath -Raw | ConvertFrom-Json
            $candidateBlob = $candidate.result.blocktemplate_blob
            if ($candidateBlob -eq $capture.result.blocktemplate_blob -or
                $candidate.result.nonce_hex -ne '01020304') {
                throw 'Candidate was not modified as required'
            }
            if ($reservedMode) {
                if ($candidate.result.reserve_hex -ne '1122334455667788' -or
                    $candidate.result.blockhashing_blob -eq $capture.result.blockhashing_blob -or
                    $candidateBlob.Substring(2*[int]$capture.result.reserved_offset,16) -ne
                    $candidate.result.reserve_hex) {
                    throw 'Reserved coinbase change and tree root not both present'
                }
            }
        }
        $submitRequest = @{
            jsonrpc='2.0'; id='isolated-submit'; method='submit_block';
            params=@($candidateBlob)
        } | ConvertTo-Json -Depth 5 -Compress
        $response = Invoke-RestMethod -Uri $rpc -Method Post -Body $submitRequest -ContentType 'application/json' -TimeoutSec 15
        if ((($response.PSObject.Properties.Name -contains 'error') -and $response.error) -or
            -not $response.result -or $response.result.status -ne 'OK') {
            throw 'Native daemon rejected the isolated block candidate'
        }
        $chainInfo = $null
        for ($i=0;$i -lt 30;$i++) {
            $infoRequest = @{jsonrpc='2.0';id='chain-check';method='get_info'} | ConvertTo-Json -Compress
            $chainInfo = Invoke-RestMethod -Uri $rpc -Method Post -Body $infoRequest -ContentType 'application/json' -TimeoutSec 2
            if ([int64]$chainInfo.result.height -ge 2) { break }
            Start-Sleep -Milliseconds 200
        }
        if (-not $chainInfo -or [int64]$chainInfo.result.height -lt 2) {
            throw 'Block submission returned OK but canonical height did not advance'
        }
        $headerRequest = @{
            jsonrpc='2.0'; id='header-check'; method='get_block_header_by_height';
            params=@{height=1}
        } | ConvertTo-Json -Depth 5 -Compress
        $headerResponse = Invoke-RestMethod -Uri $rpc -Method Post -Body $headerRequest -ContentType 'application/json' -TimeoutSec 5
        $acceptedHash = $headerResponse.result.block_header.hash
        if ($acceptedHash -notmatch '^[0-9a-fA-F]{64}$') {
            throw 'Block 1 canonical hash unavailable'
        }
        Write-Output ('PASS: native isolated block accepted at height 1; block_hash='+$acceptedHash)
        Write-Output ('DISPOSABLE_CHAIN_ONLY: no public peers, pool, payouts, or production mining')
    }
    Write-Output ('PASS: real isolated native template captured; height='+$capture.result.height+
                  ' difficulty='+$capture.result.difficulty+
                  ' hashing_bytes='+($capture.result.blockhashing_blob.Length/2))
    Write-Output ('Private template path: '+$captureFile)
} finally {
    if ($process -ne $null) {
        if (-not $process.HasExited) {
            try {
                $request = @{jsonrpc='2.0';id='stop';method='stop_daemon'} | ConvertTo-Json -Compress
                Invoke-RestMethod -Uri $rpc -Method Post -Body $request -ContentType 'application/json' -TimeoutSec 2 | Out-Null
            } catch {}
            if (-not $process.WaitForExit(5000)) {
                $process.Kill()
                $process.WaitForExit()
            }
        }
        $output = $outTask.GetAwaiter().GetResult()
        $errorText = $errTask.GetAwaiter().GetResult()
        [IO.File]::WriteAllText($stdoutFile,$output)
        [IO.File]::WriteAllText($stderrFile,$errorText)
        $process.Dispose()
        Write-Output 'Isolated daemon stopped; no ongoing test service'
    }
}
