package org.forgecoin.p2ptest;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;
import javax.crypto.AEADBadTagException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
@RunWith(AndroidJUnit4.class)
public class SolanaEncryptedVaultInstrumentedTest {
 @Test public void roundTripAndTamperRejection() throws Exception {
  byte[] secret="DISPOSABLE-TEST-SECRET".getBytes(StandardCharsets.UTF_8);
  String envelope=SolanaEncryptedVault.encrypt(secret);
  byte[] recovered=SolanaEncryptedVault.decrypt(envelope);
  assertArrayEquals(secret,recovered);
  String[] fields=envelope.split(":",-1);
  byte[] bytes=android.util.Base64.decode(fields[2],android.util.Base64.NO_WRAP);
  bytes[bytes.length-1]^=1;
  String changed=fields[0]+":"+fields[1]+":"+android.util.Base64.encodeToString(bytes,android.util.Base64.NO_WRAP);
  boolean failed=false;
  try{SolanaEncryptedVault.decrypt(changed);}catch(java.security.GeneralSecurityException expected){failed=true;}
  assertTrue("Modified GCM authentication tag must fail",failed);
  Arrays.fill(secret,(byte)0);Arrays.fill(recovered,(byte)0);
 }
}
