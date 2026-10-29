package org.forgecoin.p2ptest;
import org.junit.Test;
import static org.junit.Assert.*;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import java.nio.charset.StandardCharsets;

/** Software JCE tests prove envelope/operation behavior, not Android authentication. */
public class SolanaAuthenticatedVaultTest {
 private static Cipher cipher(int mode,SecretKey key,byte[] iv) throws Exception {
  Cipher c=Cipher.getInstance("AES/GCM/NoPadding");
  if(iv==null)c.init(mode,key); else c.init(mode,key,new GCMParameterSpec(128,iv));
  c.updateAAD(SolanaVaultEnvelope.aad()); return c;
 }
 private static SecretKey key() throws Exception {
  KeyGenerator g=KeyGenerator.getInstance("AES");g.init(256);return g.generateKey();
 }
 @Test public void roundTripAndSingleUse() throws Exception {
  SecretKey key=key();byte[] plain="synthetic QA material".getBytes(StandardCharsets.UTF_8);
  Cipher enc=cipher(Cipher.ENCRYPT_MODE,key,null);
  SolanaAuthenticatedVault.Operation op=new SolanaAuthenticatedVault.Operation(enc,plain,true);
  SolanaVaultEnvelope envelope=SolanaVaultEnvelope.parse(new String(op.finish(enc),StandardCharsets.US_ASCII));
  assertThrows(IllegalStateException.class,() -> op.finish(enc));
  Cipher dec=cipher(Cipher.DECRYPT_MODE,key,envelope.iv());
  SolanaAuthenticatedVault.Operation read=new SolanaAuthenticatedVault.Operation(dec,envelope.ciphertext(),false);
  assertArrayEquals(plain,read.finish(dec));
 }
 @Test public void mismatchAndCancellationConsumeOperation() throws Exception {
  Cipher c=cipher(Cipher.ENCRYPT_MODE,key(),null);
  SolanaAuthenticatedVault.Operation op=new SolanaAuthenticatedVault.Operation(c,new byte[]{1},true);
  assertThrows(SecurityException.class,() -> op.finish(null));
  assertThrows(IllegalStateException.class,() -> op.finish(c));
  SolanaAuthenticatedVault.Operation cancelled=new SolanaAuthenticatedVault.Operation(c,new byte[]{1},true);
  cancelled.close(); cancelled.close();
  assertThrows(IllegalStateException.class,() -> cancelled.finish(c));
 }
 @Test public void tamperingWrongKeyAndHeaderFail() throws Exception {
  SecretKey k=key();Cipher enc=cipher(Cipher.ENCRYPT_MODE,k,null);
  byte[] ct=enc.doFinal(new byte[]{1});ct[0]^=1;
  Cipher dec=cipher(Cipher.DECRYPT_MODE,k,enc.getIV());
  assertThrows(javax.crypto.AEADBadTagException.class,() -> dec.doFinal(ct));
  Cipher original=cipher(Cipher.ENCRYPT_MODE,k,null);
  byte[] good=original.doFinal(new byte[]{1});
  Cipher wrong=cipher(Cipher.DECRYPT_MODE,key(),original.getIV());
  assertThrows(javax.crypto.AEADBadTagException.class,() -> wrong.doFinal(good));
  Cipher noHeader=Cipher.getInstance("AES/GCM/NoPadding");noHeader.init(Cipher.ENCRYPT_MODE,k);
  byte[] unbound=noHeader.doFinal(new byte[]{1});
  Cipher bound=cipher(Cipher.DECRYPT_MODE,k,noHeader.getIV());
  assertThrows(javax.crypto.AEADBadTagException.class,() -> bound.doFinal(unbound));
 }
 @Test public void strictParsingAndDefensiveCopies() {
  byte[] iv=new byte[12],ct=new byte[17];
  SolanaVaultEnvelope e=SolanaVaultEnvelope.of(iv,ct);String wire=e.encode();
  iv[0]=1;ct[0]=1;e.iv()[0]=2;e.ciphertext()[0]=2;
  assertEquals(wire,e.encode());assertEquals(wire,SolanaVaultEnvelope.parse(wire).encode());
  for(String bad:new String[]{null,"",wire+":extra",wire.replace("auth-gcm-v2","gcm-v1"),wire.replace("AAAAAAAAAAAAAAAA:","AAAAAAAAAAAAAAAA=:"),new String(new char[87441]).replace('\0','x')})
   assertThrows(IllegalArgumentException.class,() -> SolanaVaultEnvelope.parse(bad));
  assertThrows(IllegalArgumentException.class,() -> SolanaVaultEnvelope.of(new byte[11],new byte[17]));
  assertThrows(IllegalArgumentException.class,() -> SolanaVaultEnvelope.of(new byte[12],new byte[16]));
 }
}
