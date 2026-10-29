package org.forgecoin.p2ptest;
import android.content.Context;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.regex.Pattern;
/** Encrypted envelopes only: private files, atomic replacement, no external storage. */
public final class SolanaVaultFiles {
 private static final Pattern NAME=Pattern.compile("[a-zA-Z0-9_-]{1,48}");
 private SolanaVaultFiles(){}
 private static File file(Context context,String name) {
  if(name==null||!NAME.matcher(name).matches())throw new IllegalArgumentException("Invalid wallet name");
  return new File(context.getNoBackupFilesDir(),"solana-"+name+".vault");
 }
 public static void saveNew(Context context,String name,String envelope) throws IOException {
  if(envelope==null||!envelope.startsWith("forgecoin-solana-android-gcm-v1:"))
   throw new IllegalArgumentException("Encrypted envelope required");
  File target=file(context,name);
  if(target.exists())throw new IOException("Wallet already exists");
  File dir=target.getParentFile();
  if(!dir.isDirectory()&&!dir.mkdirs())throw new IOException("Cannot create private vault directory");
  File temp=File.createTempFile("solana-pending-",".tmp",dir);
  boolean committed=false;
  try{
   try(FileOutputStream out=new FileOutputStream(temp)){
    out.write(envelope.getBytes(StandardCharsets.UTF_8));out.getFD().sync();
   }
   if(target.exists())throw new IOException("Wallet already exists");
   if(!temp.renameTo(target))throw new IOException("Could not commit encrypted wallet");
   committed=true;
  } finally {if(!committed)temp.delete();}
 }
 public static String read(Context context,String name)throws IOException {
  File source=file(context,name);
  if(!source.isFile()||source.length()>65536)throw new IOException("Wallet file missing or oversized");
  byte[] bytes=new byte[(int)source.length()];
  try(FileInputStream in=new FileInputStream(source)){
   int offset=0;
   while(offset<bytes.length){
    int count=in.read(bytes,offset,bytes.length-offset);
    if(count<0)throw new EOFException("Wallet truncated");
    offset+=count;
   }
  }
  return new String(bytes,StandardCharsets.UTF_8);
 }
}
