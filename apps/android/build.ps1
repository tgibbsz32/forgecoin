# ForgeCoin Android reproducible QA build using existing SDK.
# Does NOT include working wallet keys, miner, production signatures.
param([string]$OutputApk = "")
$ErrorActionPreference = 'Stop'
$AppRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$AppRoot\..\..").Path
$AndroidSdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$Tools = Join-Path $AndroidSdk 'build-tools\36.1.0'
$AndroidJar = Join-Path $AndroidSdk 'platforms\android-36.1\android.jar'
$Jbr = 'C:\Program Files\Android\Android Studio\jbr\bin'
$Manifest = Join-Path $AppRoot 'src\main\AndroidManifest.xml'
$Res = Join-Path $AppRoot 'src\main\res'
$Src = Join-Path $AppRoot 'src\main\java'
$Build = Join-Path $AppRoot 'build'
$Gen = Join-Path $Build 'gen'
$Classes = Join-Path $Build 'classes'
$Dex = Join-Path $Build 'dex'
if (-not $OutputApk) { $OutputApk = Join-Path $env:USERPROFILE 'Downloads\ForgeCoin-Android-Monitor-QA-v0.1-20261027.apk' }
if (Test-Path -LiteralPath $OutputApk) { throw 'Output exists; refusing to overwrite QA artifact.' }
foreach ($p in @($AndroidJar,"$Tools\aapt.exe","$Tools\zipalign.exe",
                 "$Tools\lib\d8.jar","$Tools\lib\apksigner.jar",
                 "$Jbr\javac.exe","$Jbr\jar.exe","$Jbr\java.exe","$Jbr\keytool.exe")) {
    if (-not (Test-Path -LiteralPath $p)) { throw "Missing Android prerequisite: $p" }
}
$logo = Join-Path $RepoRoot 'docs\images\forgecoin-logo.png'
if (-not (Test-Path -LiteralPath $logo)) { throw 'Official ForgeCoin logo not found' }
Copy-Item -LiteralPath $logo -Destination (Join-Path $Res 'drawable-nodpi\forgecoin_logo.png') -Force
foreach($p in @($Build,$Gen,$Classes,$Dex)) {
    New-Item -ItemType Directory -Force -Path $p | Out-Null
}
function Check-Exit($desc) {
    if($LASTEXITCODE -ne 0){throw "$desc failed with status $LASTEXITCODE"}
}
$resourcePackage = Join-Path $Build 'resources.ap_'
& "$Tools\aapt.exe" package -f -m -J $Gen -M $Manifest -S $Res -I $AndroidJar -F $resourcePackage
Check-Exit 'AAPT packaging'
$javaFiles=@(
    (Join-Path $Src 'org\forgecoin\mobile\qa\MainActivity.java'),
    (Join-Path $Gen 'org\forgecoin\mobile\qa\R.java')
)
& "$Jbr\javac.exe" --release 8 -encoding UTF-8 -cp $AndroidJar -d $Classes @javaFiles
Check-Exit 'Java compilation'
$classJar=Join-Path $Build 'classes.jar'
& "$Jbr\jar.exe" cf $classJar -C $Classes .
Check-Exit 'JAR assembly'
& "$Jbr\java.exe" -cp "$Tools\lib\d8.jar" com.android.tools.r8.D8 --min-api 26 --lib $AndroidJar --output $Dex $classJar
Check-Exit 'D8 bytecode conversion'
$unsigned=Join-Path $Build 'app-unsigned.apk'
$aligned=Join-Path $Build 'app-aligned.apk'
Copy-Item -LiteralPath $resourcePackage -Destination $unsigned -Force
Push-Location $Dex
try {
    & "$Tools\aapt.exe" add $unsigned 'classes.dex'
    Check-Exit 'DEX APK packaging'
} finally { Pop-Location }
& "$Tools\zipalign.exe" -f 4 $unsigned $aligned
Check-Exit 'ZIP alignment'
$keystore = Join-Path $env:USERPROFILE '.android\debug.keystore'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $keystore) | Out-Null
if(-not (Test-Path -LiteralPath $keystore)) {
    & "$Jbr\keytool.exe" -genkeypair -noprompt -keystore $keystore -storepass android -keypass android -alias androiddebugkey -dname 'CN=Android Debug,O=Android,C=US' -keyalg RSA -keysize 2048 -validity 10000
    Check-Exit 'QA debug keystore generation'
}
& "$Jbr\java.exe" -jar "$Tools\lib\apksigner.jar" sign --ks $keystore --ks-key-alias androiddebugkey --ks-pass 'pass:android' --key-pass 'pass:android' --out $OutputApk $aligned
Check-Exit 'QA APK signing'
& "$Jbr\java.exe" -jar "$Tools\lib\apksigner.jar" verify --verbose $OutputApk
Check-Exit 'APK signature verification'
& "$Tools\aapt.exe" dump badging $OutputApk | Select-String -Pattern "^package:", "^sdkVersion:", "^targetSdkVersion:", "^application-label:"
Check-Exit 'APK manifest verification'
$artifact=Get-Item -LiteralPath $OutputApk
Write-Output ('QA_APK_FILE='+$artifact.FullName)
Write-Output ('QA_APK_BYTES='+$artifact.Length)
Write-Output ('QA_APK_SHA256='+(Get-FileHash -LiteralPath $artifact.FullName -Algorithm SHA256).Hash)
Write-Output 'QA_ONLY_NO_WALLET_KEYS_NO_RANDOMX_MINING_NO_PRODUCTION_SIGNATURE'
