package org.forgecoin.p2ptest;

import android.app.Activity;
import android.hardware.biometrics.BiometricManager;
import android.hardware.biometrics.BiometricPrompt;
import android.os.Build;
import android.os.CancellationSignal;
import java.util.concurrent.atomic.AtomicBoolean;

/** API 30+ experimental adapter. Not connected to wallet UI or disk storage. */
public final class SolanaVaultPrompt {
 private SolanaVaultPrompt() {}
 public interface Result {
  void success(byte[] value);
  void failure(Exception error);
 }
 public static CancellationSignal authenticate(Activity activity,
     SolanaAuthenticatedVault.Operation operation,Result result) {
  CancellationSignal cancellation=new CancellationSignal();
  AtomicBoolean completed=new AtomicBoolean();
  java.util.function.Consumer<Exception> fail=error -> {
   if(completed.compareAndSet(false,true)) { operation.close(); result.failure(error); }
  };
  cancellation.setOnCancelListener(() -> fail.accept(new java.util.concurrent.CancellationException("Authentication cancelled")));
  try {
   if(Build.VERSION.SDK_INT<30)throw new UnsupportedOperationException("API 30+ required");
   BiometricManager manager=activity.getSystemService(BiometricManager.class);
   if(manager==null || manager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)!=BiometricManager.BIOMETRIC_SUCCESS)
    throw new IllegalStateException("Strong biometric unavailable");
   BiometricPrompt prompt=new BiometricPrompt.Builder(activity)
    .setTitle("Unlock test vault")
    .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG)
    .setNegativeButton("Cancel",activity.getMainExecutor(),(dialog,which) -> cancellation.cancel()).build();
   prompt.authenticate(new BiometricPrompt.CryptoObject(operation.cipher()),cancellation,
    activity.getMainExecutor(),new BiometricPrompt.AuthenticationCallback() {
     @Override public void onAuthenticationError(int code,CharSequence message) {
      fail.accept(new SecurityException("Biometric authentication error: "+code));
     }
     @Override public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult auth) {
      if(!completed.compareAndSet(false,true))return;
      byte[] value;
      try {
       BiometricPrompt.CryptoObject crypto=auth.getCryptoObject();
       value=operation.finish(crypto==null?null:crypto.getCipher());
      } catch(Exception error) { operation.close(); result.failure(error); return; }
      result.success(value);
     }
     // A nonmatching biometric is retryable; it never completes the cipher.
    });
  } catch(Exception error) { fail.accept(error); }
  return cancellation;
 }
}
