package org.forgecoin.p2ptest;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import android.content.Context;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;
import java.util.*;
@RunWith(AndroidJUnit4.class)
public class SolanaWalletLifecycleInstrumentedTest {
 @Test public void createRestoreSameAddress() throws Exception{
  Context ctx=InstrumentationRegistry.getInstrumentation().getTargetContext();
  String one="qa-create-"+System.nanoTime(),two="qa-restore-"+System.nanoTime();
  try{
   SolanaWalletLifecycle.Created created=SolanaWalletLifecycle.create(ctx,one);
   assertEquals(12,created.phrase.split(" ").length);
   assertEquals(created.address,SolanaWalletLifecycle.addressFromStored(ctx,one));
   SolanaWalletLifecycle.Created restored=SolanaWalletLifecycle.restore(ctx,two,created.phrase);
   assertEquals(created.address,restored.address);
   assertEquals(created.address,SolanaWalletLifecycle.addressFromStored(ctx,two));
   boolean failed=false;
   try{SolanaWalletLifecycle.restore(ctx,"qa-invalid-"+System.nanoTime(),created.phrase.replaceFirst("^[^ ]+","zoo"));}
   catch(IllegalArgumentException expected){failed=true;}
   assertTrue("Mutated phrase must be rejected",failed);
  } finally{
   new java.io.File(ctx.getNoBackupFilesDir(),"solana-"+one+".vault").delete();
   new java.io.File(ctx.getNoBackupFilesDir(),"solana-"+two+".vault").delete();
  }
 }
}
