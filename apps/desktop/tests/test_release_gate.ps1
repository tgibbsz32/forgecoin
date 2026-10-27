# GUI release-gate test using FAKE local binary fixtures, no keys or mining.
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$src = Get-Content -Raw -LiteralPath (Join-Path $project 'apps\desktop\Program.cs')
$solana = Join-Path $project 'apps\desktop\SolanaWalletTab.cs'
$csc = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$work = Join-Path $env:TEMP ('forgecoin-release-gate-test-'+[guid]::NewGuid().ToString('N'))
function Assert([bool]$condition,[string]$description) {
    if (-not $condition){throw "FAIL: $description"}
}
function Build([string]$dir,[string]$name,[string]$source) {
    [System.IO.Directory]::CreateDirectory($dir) | Out-Null
    [System.IO.Directory]::CreateDirectory((Join-Path $dir 'bin')) | Out-Null
    $program = Join-Path $dir 'Program.cs'
    [System.IO.File]::WriteAllText($program,$source,[System.Text.Encoding]::UTF8)
    $output = Join-Path $dir ($name+'.exe')
    $args = @('/nologo','/target:winexe','/optimize+','/platform:anycpu',("/out:"+$output),
       '/reference:System.dll','/reference:System.Core.dll','/reference:System.Drawing.dll',
       '/reference:System.Windows.Forms.dll','/reference:System.Web.Extensions.dll',$program,$solana)
    & $csc @args
    Assert ($LASTEXITCODE -eq 0) "C# compilation"
    return $output
}
function WidgetState([string]$exe) {
    # Separate process unloads the inspected executable before temp cleanup.
    $probe=Join-Path $work 'probe.ps1'
    $answer = & "$PSHOME\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $probe -Exe $exe
    Assert ($LASTEXITCODE -eq 0) "isolated reflection probe"
    $parts = ([string]$answer).Trim().Split(',')
    Assert ($parts.Count -eq 2) "reflection output"
    return @(($parts[0] -eq '1'),($parts[1] -eq '1'))
}
function Fixture([string]$dir) {
    $m=Get-Content (Join-Path $project 'config\mainnet.identity.json') -Raw | ConvertFrom-Json
    $m.stage='released';$m.release_authorized=$true
    $checks=@{}
    foreach($name in @('forged.exe','forge-wallet-rpc.exe','forge-wallet-cli.exe')) {
        $file=Join-Path (Join-Path $dir 'bin') $name
        [System.IO.File]::WriteAllText($file,"FAKE QA INPUT - NEVER EXECUTE - "+$name)
        $checks[$name]=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $m | Add-Member -NotePropertyName windows_release_binaries_sha256 -NotePropertyValue $checks -Force
    $path=Join-Path $dir 'mainnet.identity.json'
    [System.IO.File]::WriteAllText($path,($m | ConvertTo-Json -Depth 20),[System.Text.Encoding]::UTF8)
    return $path
}
try {
    [System.IO.Directory]::CreateDirectory($work)|Out-Null
    $probeText=@'
param([string]$Exe)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
$asm=[System.Reflection.Assembly]::LoadFrom($Exe)
$type=$asm.GetType('ForgeCoinDesktop.MainForm')
if($null -eq $type){throw 'Form not found'}
$form=[Activator]::CreateInstance($type,$true)
try {
    $flags=[System.Reflection.BindingFlags]'Instance,NonPublic'
    $solo=$type.GetField('startMiningButton',$flags).GetValue($form)
    $pool=$type.GetField('startPoolButton',$flags).GetValue($form)
    Write-Output (([int]$solo.Enabled).ToString()+','+([int]$pool.Enabled).ToString())
} finally { $form.Dispose() }
'@
    [System.IO.File]::WriteAllText((Join-Path $work 'probe.ps1'),$probeText,[System.Text.Encoding]::UTF8)
    $locked=Join-Path $work 'locked'
    $approved=Join-Path $work 'approved'
    $lockedExe=Build $locked 'ForgeCoin-Locked-Reflection-QA' $src
    $approvedSrc=$src.Replace('private static readonly bool BuildPermitsPublicMining = false;',
         'private static readonly bool BuildPermitsPublicMining = true;')
    Assert ($approvedSrc -ne $src) 'temp test must replace just the build flag'
    $approvedExe=Build $approved 'ForgeCoin-Release-Reflection-QA' $approvedSrc
    $l=Fixture $locked
    $p=Fixture $approved
    $s=WidgetState $lockedExe
    Assert ((-not $s[0]) -and (-not $s[1])) 'QA executable remains locked even with fake release JSON'
    Write-Output 'PASS locked QA build ignores locally edited release metadata'
    $s=WidgetState $approvedExe
    Assert ($s[0] -and $s[1]) 'test-only build with exact hashes and release manifest unlocks buttons'
    Write-Output 'PASS simulated reviewed release requires exact manifest and local SHA256 pins'
    $file=Join-Path $approved 'bin\forged.exe'
    [System.IO.File]::AppendAllText($file,'QA tamper')
    $s=WidgetState $approvedExe
    Assert ((-not $s[0]) -and (-not $s[1])) 'binary tamper disables mining'
    Write-Output 'PASS tampered native daemon makes mining controls unavailable'
    $approvedManifest=Get-Content -LiteralPath $p -Raw | ConvertFrom-Json
    $approvedManifest.genesis_hash='0'*64
    [System.IO.File]::WriteAllText($p,($approvedManifest | ConvertTo-Json -Depth 20),[System.Text.Encoding]::UTF8)
    $s=WidgetState $approvedExe
    Assert ((-not $s[0]) -and (-not $s[1])) 'wrong genesis disables mining'
    Write-Output 'PASS wrong-genesis manifest does not unlock mining'
    Write-Output 'RELEASE_GATE_REFLECTION_TESTS_PASS - simulated inputs only, no daemon started'
} finally {
    if(Test-Path -LiteralPath $work){Remove-Item -LiteralPath $work -Recurse -Force}
}
