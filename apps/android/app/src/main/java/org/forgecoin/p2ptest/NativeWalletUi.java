package org.forgecoin.p2ptest;
import android.app.Activity;
import android.app.AlertDialog;
import android.text.InputType;
import android.view.WindowManager;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.*;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicBoolean;

/** Native wallet lifecycle and balance sync confined to disposable development chains. */
final class NativeWalletUi {
    private static final AtomicBoolean BUSY=new AtomicBoolean();
    private NativeWalletUi(){}
    private static EditText input(Activity a,String hint,boolean secret) {
        EditText v=new EditText(a);v.setHint(hint);
        v.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS |
            (secret?InputType.TYPE_TEXT_VARIATION_PASSWORD:InputType.TYPE_TEXT_FLAG_MULTI_LINE));
        v.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS);
        v.setImeOptions(EditorInfo.IME_FLAG_NO_PERSONALIZED_LEARNING);
        return v;
    }
    private static String path(Activity a) throws Exception {
        File dir=new File(a.getFilesDir(),"native-frg-wallet");
        if(!dir.isDirectory() && !dir.mkdirs())throw new IllegalStateException("Private storage unavailable");
        return new File(dir,"wallet").getCanonicalPath();
    }
    static void create(Activity a,TextView status){ask(a,status,0);}
    static void restore(Activity a,TextView status){ask(a,status,1);}
    static void unlock(Activity a,TextView status){ask(a,status,2);}
    static void sync(Activity a,TextView status){ask(a,status,3);}
    private static void ask(Activity a,TextView status,int operation) {
        if(!BuildConfig.DEBUG || !NativeFrgWallet.available() || BUSY.get())return;
        a.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        LinearLayout form=new LinearLayout(a);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(24,12,24,12);
        EditText password=input(a,"Wallet password (at least 12 UTF-8 bytes)",true);form.addView(password);
        EditText confirm=input(a,"Confirm wallet password",true);
        EditText seed=input(a,"25-word native FRG recovery phrase",true);
        if(operation<2)form.addView(confirm);
        if(operation==1)form.addView(seed);
        EditText node=input(a,"Loopback FAKECHAIN daemon port",false);
        node.setInputType(InputType.TYPE_CLASS_NUMBER);
        if(operation==3)form.addView(node);
        AlertDialog dialog=new AlertDialog.Builder(a)
            .setTitle(operation==0?"Create native FRG wallet":operation==1?"Restore native FRG wallet":operation==2?"Unlock FRG receiving address":"Sync isolated FRG wallet")
            .setMessage("Development wallet for a disposable offline ForgeCoin chain. Keep your password and a written 25-word backup.")
            .setView(form).setNegativeButton("Cancel",null).setPositiveButton("Continue",null).create();
        dialog.setOnDismissListener(d->{password.setText("");confirm.setText("");seed.setText("");});
        dialog.setOnShowListener(d->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
            byte[] pw=password.getText().toString().getBytes(StandardCharsets.UTF_8);
            String phrase=seed.getText().toString().trim();
            if(pw.length<12 || pw.length>1024 || (operation<2 &&
                    !password.getText().toString().equals(confirm.getText().toString()))) {
                Arrays.fill(pw,(byte)0);password.setError("Use matching passwords of 12-1024 UTF-8 bytes");return;
            }
            if(operation==1) {
                try{FrgSeedVault.validateRecoveryPhrase(phrase.toCharArray());}
                catch(IllegalArgumentException ex){Arrays.fill(pw,(byte)0);seed.setError(ex.getMessage());return;}
            }
            final int port;
            try {
                port=operation==3?Integer.parseInt(node.getText().toString().trim()):0;
                if(operation==3 && (port<1024 || port>65535))throw new NumberFormatException();
            } catch(NumberFormatException error){
                Arrays.fill(pw,(byte)0);node.setError("Enter a disposable loopback port from 1024 to 65535");return;
            }
            if(!BUSY.compareAndSet(false,true)){Arrays.fill(pw,(byte)0);return;}
            dialog.dismiss();status.setText("Working with encrypted native wallet...");
            new Thread(()->{
                long handle=0;String address=null,recovery=null,balance=null;boolean ok=false;
                try {
                    String file=path(a);
                    if(operation==0)handle=NativeFrgWallet.create(file,pw);
                    else if(operation==1)handle=NativeFrgWallet.restore(file,pw,phrase,0);
                    else handle=NativeFrgWallet.open(file,pw);
                    address=NativeFrgWallet.address(handle);
                    if(operation==3) {
                        String[] scan=NativeFrgWallet.refreshQaNode(handle,port).split(":");
                        balance="Isolated balance: "+frg(scan[0])+" FRG, unlocked "+frg(scan[1])
                            +" FRG\nWallet height: "+scan[2];
                    } else recovery=NativeFrgWallet.seed(handle);
                    NativeFrgWallet.close(handle);handle=0;ok=true;
                } catch(Exception | LinkageError ex) {
                    // No exception details, credentials or recovery data enter diagnostics.
                } finally {
                    if(handle!=0)try{NativeFrgWallet.close(handle);}catch(RuntimeException ignored){}
                    Arrays.fill(pw,(byte)0);BUSY.set(false);
                }
                final boolean success=ok;final String receiving=address,backup=recovery,synchronizedBalance=balance;
                a.runOnUiThread(()->{
                    if(a.isFinishing() || a.isDestroyed())return;
                    if(!success){status.setText("Native wallet operation failed. Check password, phrase/checksum and existing wallet. Existing files were preserved.");return;}
                    status.setText("Native FRG receiving address:\n"+receiving+"\n"+
                        (synchronizedBalance==null?"Not synchronized":synchronizedBalance));
                    status.setTextIsSelectable(true);
                    if(backup!=null)showBackup(a,backup);
                });
            },"native-frg-offline-wallet").start();
        }));
        dialog.show();dialog.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
    }
    private static String frg(String atomic) {
        return new java.math.BigDecimal(atomic).movePointLeft(8).stripTrailingZeros().toPlainString();
    }
    private static void showBackup(Activity a,String phrase) {
        TextView text=new TextView(a);text.setPadding(24,12,24,12);text.setText(phrase);text.setTextSize(18);
        text.setTextIsSelectable(false);
        AlertDialog dialog=new AlertDialog.Builder(a).setTitle("Write down all 25 words in order")
            .setMessage("This recovers your FRG wallet. Do not share these words. The encrypted wallet is stored on this device; automatic Android backups are disabled.")
            .setView(text).setNegativeButton("Close",null)
            .setPositiveButton("Verify written backup",(d,w)->confirmBackup(a,phrase)).create();
        dialog.setOnDismissListener(d->text.setText(""));
        dialog.show();dialog.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
    }
    private static void confirmBackup(Activity a,String expected) {
        EditText typed=input(a,"Re-enter all 25 words from your written backup",true);
        AlertDialog dialog=new AlertDialog.Builder(a).setTitle("Verify FRG recovery backup").setView(typed)
            .setNegativeButton("Cancel",null).setPositiveButton("Verify",null).create();
        dialog.setOnDismissListener(d->typed.setText(""));
        dialog.setOnShowListener(d->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
            String actual=typed.getText().toString().trim().replaceAll("\\s+"," ");
            if(!expected.equals(actual)){typed.setError("Words do not match the native wallet backup");return;}
            Toast.makeText(a,"Written recovery backup verified",Toast.LENGTH_LONG).show();dialog.dismiss();
        }));
        dialog.show();dialog.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
    }
}
