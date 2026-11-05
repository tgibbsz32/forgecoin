package org.forgecoin.p2ptest;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import android.content.Context;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.UUID;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

/** Offline JNI wallet lifecycle. Never logs a seed or contacts a network. */
@RunWith(AndroidJUnit4.class)
public class NativeFrgWalletInstrumentedTest {
    @Test public void synchronizesReceivedFrgFromDisposableChain() throws Exception {
        String endpoint=InstrumentationRegistry.getArguments().getString("frgWalletEndpoint");
        org.junit.Assume.assumeTrue("Disposable FAKECHAIN node required",endpoint!=null);
        assertTrue(endpoint.startsWith("127.0.0.1:"));
        int port=Integer.parseInt(endpoint.substring("127.0.0.1:".length()));
        FrgQaNode.requireIsolated(port);
        assertTrue(NativeFrgWallet.available());
        Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();
        File dir=new File(c.getFilesDir(),"native-wallet-sync-test-"+UUID.randomUUID());
        assertTrue(dir.mkdir());
        byte[] password="disposable-sync-test-password".getBytes(StandardCharsets.UTF_8);
        long created=0,restored=0;
        try {
            created=NativeFrgWallet.create(new File(dir,"source").getAbsolutePath(),password);
            String address=NativeFrgWallet.address(created);
            restored=NativeFrgWallet.restore(new File(dir,"restored").getAbsolutePath(),
                password,NativeFrgWallet.seed(created),0);
            org.json.JSONObject args=new org.json.JSONObject().put("amount_of_blocks",1)
                .put("wallet_address",address).put("starting_nonce",0).put("prev_block","");
            org.json.JSONObject result=FrgQaNode.rpc(port,"generateblocks",args,35000).getJSONObject("result");
            assertEquals("OK",result.getString("status"));
            assertEquals(1,result.getJSONArray("blocks").length());
            String[] snapshot=NativeFrgWallet.refreshQaNode(restored,port).split(":");
            assertTrue("Native wallet must detect the disposable received coinbase",
                new java.math.BigInteger(snapshot[0]).signum()>0);
            assertEquals("New coinbase must stay locked","0",snapshot[1]);
            assertTrue(Long.parseLong(snapshot[2])>=2);
        } finally {
            if(created!=0)NativeFrgWallet.close(created);
            if(restored!=0)NativeFrgWallet.close(restored);
            Arrays.fill(password,(byte)0);
            File[] files=dir.listFiles();
            if(files!=null)for(File f:files)assertTrue("Cannot remove disposable test wallet",f.delete());
            assertTrue(dir.delete());
        }
    }

    @Test public void signsConfirmsAndReceivesIsolatedTransfer() throws Exception {
        String endpoint=InstrumentationRegistry.getArguments().getString("frgWalletEndpoint");
        org.junit.Assume.assumeTrue("Disposable FAKECHAIN node required",endpoint!=null);
        int port=MiningConfiguration.loopbackPort(endpoint);
        FrgQaNode.requireIsolated(port);
        Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();
        File dir=new File(c.getFilesDir(),"native-wallet-send-test-"+UUID.randomUUID());
        assertTrue(dir.mkdir());
        byte[] password="disposable-send-test-password".getBytes(StandardCharsets.UTF_8);
        long sender=0,receiver=0;
        try {
            stage("Creating disposable sender and recipient");
            sender=createAtGenesis(dir,"sender",password);
            receiver=createAtGenesis(dir,"receiver",password);
            stage("Disposable keys created");
            String senderAddress=NativeFrgWallet.address(sender);
            String recipient=NativeFrgWallet.address(receiver);
            // Enough mature, same-chain ring members for the native wallet.
            for(int i=0;i<8;i++) {
                mine(port,senderAddress,10);
                stage("Disposable funding blocks: "+((i+1)*10));
            }
            String[] before=NativeFrgWallet.refreshQaNode(sender,port).split(":");
            stage("Sender synchronized");
            assertTrue(Long.parseLong(before[1])>100000000);
            String[] quote=NativeFrgWallet.prepareQaSend(sender,port,recipient,100000000).split(":");
            assertEquals("100000000",quote[0]);
            assertTrue(Long.parseLong(quote[1])>0);
            stage("Native transaction prepared");
            NativeFrgWallet.cancelLocal(sender);
            try{NativeFrgWallet.confirmQaSend(sender,port);fail("Canceled transaction broadcast");}
            catch(IllegalStateException expected){}
            NativeFrgWallet.prepareQaSend(sender,port,recipient,100000000);
            assertTrue(NativeFrgWallet.confirmQaSend(sender,port).matches("[a-f0-9]{64}"));
            mine(port,senderAddress,1);
            assertEquals("100000000",NativeFrgWallet.refreshQaNode(receiver,port).split(":")[0]);
        } finally {
            if(sender!=0)NativeFrgWallet.close(sender);
            if(receiver!=0)NativeFrgWallet.close(receiver);
            Arrays.fill(password,(byte)0);
            File[] files=dir.listFiles();
            if(files!=null)for(File f:files)assertTrue("Cannot remove disposable test wallet",f.delete());
            assertTrue(dir.delete());
        }
    }

    private static void stage(String message) {
        android.util.Log.i("FRGWalletAcceptance",message);
        android.os.Bundle data=new android.os.Bundle();
        data.putString("stream",message+"\n");
        InstrumentationRegistry.getInstrumentation().sendStatus(2,data);
    }

    private static long createAtGenesis(File dir,String name,byte[] password) {
        long temporary=NativeFrgWallet.create(new File(dir,name+"-generated").getAbsolutePath(),password);
        String phrase;
        try{phrase=NativeFrgWallet.seed(temporary);}
        finally{NativeFrgWallet.close(temporary);}
        return NativeFrgWallet.restore(new File(dir,name).getAbsolutePath(),password,phrase,0);
    }

    private static void mine(int port,String address,int blocks) throws Exception {
        org.json.JSONObject args=new org.json.JSONObject().put("amount_of_blocks",blocks)
            .put("wallet_address",address).put("starting_nonce",0).put("prev_block","");
        org.json.JSONObject result=FrgQaNode.rpc(port,"generateblocks",args,35000).getJSONObject("result");
        assertEquals("OK",result.getString("status"));
        assertEquals(blocks,result.getJSONArray("blocks").length());
    }

    @Test public void nativeCreateBackupRestoreAndEncryptedReopen() throws Exception {
        assertTrue("Current native FRG wallet engine must be linked",NativeFrgWallet.available());
        Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();
        File dir=new File(c.getFilesDir(),"native-wallet-test-"+UUID.randomUUID());
        assertTrue(dir.mkdir());
        byte[] password="disposable-QA-password-7d7f307".getBytes(StandardCharsets.UTF_8);
        long first=0,restored=0;
        try {
            String path=new File(dir,"created").getAbsolutePath();
            first=NativeFrgWallet.create(path,password);
            assertTrue(first>0);
            String address=NativeFrgWallet.address(first);
            assertEquals(FrgPublicAddress.Kind.STANDARD,FrgPublicAddress.parse(address).kind);
            String seed=NativeFrgWallet.seed(first);
            FrgSeedVault.validateRecoveryPhrase(seed.toCharArray());
            assertEquals("0",NativeFrgWallet.snapshot(first).split(":")[0]);
            NativeFrgWallet.close(first); first=0;
            byte[] wrong="deliberately-wrong-password".getBytes(StandardCharsets.UTF_8);
            try {NativeFrgWallet.open(path,wrong);fail("Incorrect password accepted");}
            catch(IllegalStateException expected){}
            finally {Arrays.fill(wrong,(byte)0);}
            first=NativeFrgWallet.open(path,password);
            assertEquals(address,NativeFrgWallet.address(first));
            try{NativeFrgWallet.create(path,password);fail("Wallet overwrite accepted");}
            catch(IllegalStateException expected){}
            String restoredPath=new File(dir,"restored").getAbsolutePath();
            restored=NativeFrgWallet.restore(restoredPath,password,seed,0);
            assertEquals(address,NativeFrgWallet.address(restored));
            assertEquals(seed,NativeFrgWallet.seed(restored));
            long old=restored;NativeFrgWallet.close(restored);restored=0;
            try{NativeFrgWallet.address(old);fail("Closed handle accepted");}
            catch(IllegalStateException expected){}
            String[] words=seed.split(" "); words[24]="notaword";
            try{NativeFrgWallet.restore(new File(dir,"invalid").getAbsolutePath(),password,String.join(" ",words),0);fail("Bad seed accepted");}
            catch(IllegalStateException expected){}
        } finally {
            if(first!=0)NativeFrgWallet.close(first);
            if(restored!=0)NativeFrgWallet.close(restored);
            Arrays.fill(password,(byte)0);
            File[] files=dir.listFiles();
            if(files!=null)for(File f:files)assertTrue("Cannot remove disposable test wallet",f.delete());
            assertTrue(dir.delete());
        }
    }
}
