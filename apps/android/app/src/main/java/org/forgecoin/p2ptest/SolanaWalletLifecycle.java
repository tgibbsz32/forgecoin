package org.forgecoin.p2ptest;
import android.content.Context;
import java.io.InputStream;
import java.util.Arrays;
/** Offline create/restore coordinator. No financial transactions and no UI exposure yet. */
public final class SolanaWalletLifecycle {
 private SolanaWalletLifecycle(){}
 public static final class Created {
  public final String phrase,address;
  private Created(String phrase,String address){this.phrase=phrase;this.address=address;}
 }
 private static String[] words(Context ctx)throws Exception{
  try(InputStream in=ctx.getAssets().open("bip39-english.txt")){return SolanaMnemonicCheck.load(in);}
 }
 public static Created create(Context ctx,String name)throws Exception{
  String[] w=words(ctx);
  String phrase=SolanaMnemonicGenerate.create(w);
  return restore(ctx,name,phrase);
 }
 public static Created restore(Context ctx,String name,String phrase)throws Exception{
  String[] w=words(ctx);
  if(!SolanaMnemonicCheck.valid(phrase,w))throw new IllegalArgumentException("Invalid mnemonic");
  String address=SolanaPublicAddress.fromPhrase(phrase,w,0);
  // The current proof-of-concept vault stores a derivation phrase, not a signing key.
  // It is not authorized for real-wallet custody, or for Android GUI activation.
  byte[] raw=phrase.getBytes(java.nio.charset.StandardCharsets.UTF_8);
  try{
   String envelope=SolanaEncryptedVault.encrypt(raw);
   SolanaVaultFiles.saveNew(ctx,name,envelope);
  } finally {Arrays.fill(raw,(byte)0);}
  return new Created(phrase,address);
 }
 public static String addressFromStored(Context ctx,String name)throws Exception{
  byte[] raw=SolanaEncryptedVault.decrypt(SolanaVaultFiles.read(ctx,name));
  try{
   String phrase=new String(raw,java.nio.charset.StandardCharsets.UTF_8);
   return SolanaPublicAddress.fromPhrase(phrase,words(ctx),0);
  } finally {Arrays.fill(raw,(byte)0);}
 }
}
