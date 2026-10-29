package org.forgecoin.p2ptest;
import android.app.Activity;
import android.app.KeyguardManager;
import android.hardware.biometrics.BiometricManager;
import android.hardware.biometrics.BiometricPrompt;
import android.os.Build;
import android.os.CancellationSignal;
import android.widget.Toast;
/** Test-UI access gate, NOT Keystore-bound authentication or production custody. */
public final class SolanaDebugAuthGate {
 private SolanaDebugAuthGate(){}
 public static void require(Activity activity,Runnable allowed){
  if(!BuildConfig.DEBUG || Build.VERSION.SDK_INT<30){
   Toast.makeText(activity,"Device authentication unavailable in this test build",Toast.LENGTH_LONG).show();return;
  }
  KeyguardManager lock=activity.getSystemService(KeyguardManager.class);
  if(lock==null||!lock.isDeviceSecure()){
   Toast.makeText(activity,"Set up a secure device screen lock before testing wallets",Toast.LENGTH_LONG).show();return;
  }
  BiometricPrompt prompt=new BiometricPrompt.Builder(activity)
   .setTitle("Authorize ForgeCoin test wallet")
   .setSubtitle("Development-only operation — do not deposit funds")
   .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG|BiometricManager.Authenticators.DEVICE_CREDENTIAL)
   .build();
  prompt.authenticate(new CancellationSignal(),activity.getMainExecutor(),new BiometricPrompt.AuthenticationCallback(){
   @Override public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult result){
    super.onAuthenticationSucceeded(result);
    if(!activity.isFinishing()&&!activity.isDestroyed())allowed.run();
   }
   @Override public void onAuthenticationError(int errorCode,CharSequence errString){
    super.onAuthenticationError(errorCode,errString);
    Toast.makeText(activity,"Wallet test authentication did not complete",Toast.LENGTH_SHORT).show();
   }
  });
 }
}
