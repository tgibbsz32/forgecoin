package org.forgecoin.p2ptest;
import android.app.Activity;
import android.app.AlertDialog;
import android.text.InputType;
import android.view.WindowManager;
import android.widget.*;
/** Recovery confirmation UI component; intentionally not connected to production create/restore. */
public final class SolanaRecoveryConfirmDialog {
 private SolanaRecoveryConfirmDialog(){}
 public static boolean matches(String phrase,String word4,String word9){
  if(phrase==null)return false;
  String[] words=phrase.split(" ",-1);
  return words.length==12 && words[3].equals(word4==null?"":word4.trim()) &&
      words[8].equals(word9==null?"":word9.trim());
 }
 public static void show(Activity activity,String phrase,Runnable accepted){
  if(phrase==null||phrase.split(" ",-1).length!=12)throw new IllegalArgumentException("Expected 12-word BIP39 phrase");
  activity.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
  LinearLayout view=new LinearLayout(activity);view.setPadding(32,24,32,12);view.setOrientation(LinearLayout.VERTICAL);
  TextView warning=new TextView(activity);warning.setText("Write the 12 words down offline, in order. Never share or photograph them. This screen cannot recover a lost phrase.");
  view.addView(warning);
  TextView words=new TextView(activity);words.setText(phrase);words.setTextIsSelectable(false);words.setPadding(0,20,0,20);view.addView(words);
  new AlertDialog.Builder(activity).setTitle("Sensitive recovery words").setView(view)
   .setNegativeButton("Cancel",(dialog,which)->words.setText(""))
   .setPositiveButton("I wrote them down",(dialog,which)->{
      words.setText("");confirm(activity,phrase,accepted);
   }).setOnCancelListener(dialog->words.setText("")).show();
 }
 private static void confirm(Activity activity,String phrase,Runnable accepted){
  LinearLayout v=new LinearLayout(activity);v.setOrientation(LinearLayout.VERTICAL);v.setPadding(32,24,32,12);
  EditText fourth=new EditText(activity);fourth.setHint("Word 4");fourth.setSingleLine(true);fourth.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
  EditText ninth=new EditText(activity);ninth.setHint("Word 9");ninth.setSingleLine(true);ninth.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
  v.addView(fourth);v.addView(ninth);
  final AlertDialog dialog=new AlertDialog.Builder(activity).setTitle("Confirm your backup").setView(v)
   .setNegativeButton("Cancel",null).setPositiveButton("Verify",null).create();
  dialog.setOnShowListener(d->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(button->{
   boolean ok=matches(phrase,fourth.getText().toString(),ninth.getText().toString());
   fourth.setText("");ninth.setText("");
   if(ok){dialog.dismiss();accepted.run();}
   else Toast.makeText(activity,"Recovery confirmation did not match",Toast.LENGTH_LONG).show();
  }));
  dialog.show();
 }
}
