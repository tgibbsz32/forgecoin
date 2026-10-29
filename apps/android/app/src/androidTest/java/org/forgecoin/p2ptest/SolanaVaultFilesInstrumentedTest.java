package org.forgecoin.p2ptest;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;
import android.content.Context;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
@RunWith(AndroidJUnit4.class)
public class SolanaVaultFilesInstrumentedTest {
 @Test public void encryptedRecordPersistsPrivatelyAndRejectsDuplicate() throws Exception {
  Context ctx=InstrumentationRegistry.getInstrumentation().getTargetContext();
  String name="qa-"+System.nanoTime();
  byte[] disposable="DISPOSABLE-TEST-ONLY".getBytes(StandardCharsets.UTF_8);
  String encrypted=SolanaEncryptedVault.encrypt(disposable);
  SolanaVaultFiles.saveNew(ctx,name,encrypted);
  assertEquals(encrypted,SolanaVaultFiles.read(ctx,name));
  assertArrayEquals(disposable,SolanaEncryptedVault.decrypt(SolanaVaultFiles.read(ctx,name)));
  assertTrue(new java.io.File(ctx.getNoBackupFilesDir(),"solana-"+name+".vault").isFile());
  boolean rejected=false;
  try{SolanaVaultFiles.saveNew(ctx,name,encrypted);}catch(java.io.IOException expected){rejected=true;}
  assertTrue("Must not overwrite existing wallet",rejected);
  assertTrue(new java.io.File(ctx.getNoBackupFilesDir(),"solana-"+name+".vault").delete());
  Arrays.fill(disposable,(byte)0);
 }
}
