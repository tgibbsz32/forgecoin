package org.forgecoin.p2ptest;
import android.app.*;
import android.text.InputType;
import android.view.WindowManager;
import android.widget.*;
/** DEBUG-ONLY offline create/restore workflow. NEVER present as production custody. */
public final class SolanaWalletDebugFlow {
 private SolanaWalletDebugFlow(){}
 private static void notify(Activity a,String message){new AlertDialog.Builder(a).setTitle("Development-only wallet").setMessage(message).setPositiveButton("OK",null).show();}
 public static void create(Activity a){
  if(!BuildConfig.DEBUG)return;
  a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
  try{
   String name="preview-"+System.currentTimeMillis();
   SolanaWalletLifecycle.Created candidate=SolanaWalletLifecycle.create(a,name);
   SolanaRecoveryConfirmDialog.show(a,candidate.phrase,()->{
    try{
     SolanaWalletLifecycle.Created saved=SolanaWalletLifecycle.restore(a,name,candidate.phrase);
     if(!saved.address.equals(candidate.address))throw new IllegalStateException("Address mismatch");
     notify(a,"Encrypted local test wallet created after backup confirmation. Address: "+saved.address+"\nNo transactions or funds supported. Retain words safely; this build is NOT a production wallet.");
    }catch(Exception err){notify(a,"Preview save failed. Do not rely on this wallet.");}
   });
  }catch(Exception err){notify(a,"Preview create failed. No wallet created.");}
 }
 public static void restore(Activity a){
  if(!BuildConfig.DEBUG)return;
  a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
  LinearLayout v=new LinearLayout(a);v.setOrientation(LinearLayout.VERTICAL);v.setPadding(24,12,24,12);
  EditText phrase=new EditText(a);phrase.setHint("12 BIP39 words, separated by spaces");phrase.setMinLines(3);phrase.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
  v.addView(phrase);
  new AlertDialog.Builder(a).setTitle("DEV ONLY — Restore Solana test wallet").setView(v).setNegativeButton("Cancel",null)
   .setPositiveButton("Restore",(dialog,which)->{
    String entered=phrase.getText().toString().trim();phrase.setText("");
    try{
     String name="restored-"+System.currentTimeMillis();
     SolanaWalletLifecycle.Created saved=SolanaWalletLifecycle.restore(a,name,entered);
     notify(a,"Local test wallet restored. Address: "+saved.address+"\nNo transactions or funds supported.");
    }catch(Exception err){notify(a,"Recovery rejected. Verify the 12-word phrase and wallet name.");}
   }).show();
 }
}
