use aes_gcm::aead::{Aead, Payload};
use aes_gcm::{Aes256Gcm, KeyInit, Nonce};
use argon2::{Algorithm, Argon2, Params, Version};
use bip39::{Language, Mnemonic};
use ed25519_dalek::SigningKey;
use hmac::{Hmac, Mac};
use rand::{rngs::OsRng, RngCore};
use serde::{Deserialize, Serialize};
use sha2::Sha512;
use std::fs::{File, OpenOptions};
use std::io::{Read, Write};
use std::path::Path;
use zeroize::Zeroize;

const DERIVATION: &str = "m/44'/501'/0'/0'";
type HmacSha512 = Hmac<Sha512>;

#[derive(Deserialize)]
struct Request {
    op: String,
    vault_path: String,
    password: Option<String>,
    mnemonic: Option<String>,
}
#[derive(Serialize, Deserialize)]
struct Vault {
    version: u32,
    network: String,
    derivation: String,
    address: String,
    salt_hex: String,
    nonce_hex: String,
    ciphertext_hex: String,
}
#[derive(Serialize)]
struct Reply {
    ok: bool,
    address: Option<String>,
    mnemonic: Option<String>,
    error: Option<String>,
}
fn error(message: impl Into<String>) -> Reply {
    Reply { ok: false, address: None, mnemonic: None, error: Some(message.into()) }
}
fn reply(address: String, phrase: Option<String>) -> Reply {
    Reply { ok: true, address: Some(address), mnemonic: phrase, error: None }
}
fn derived_public_key(phrase: &str) -> Result<String, String> {
    let mnemonic = Mnemonic::parse_in(Language::English, phrase).map_err(|_| "Invalid BIP39 English recovery phrase or checksum")?;
    let mut seed = mnemonic.to_seed("");
    let mut mac = <HmacSha512 as Mac>::new_from_slice(b"ed25519 seed").map_err(|_| "Key derivation unavailable")?;
    mac.update(&seed);
    let mut material = mac.finalize().into_bytes();
    let mut private_key = [0u8; 32];
    let mut chain_code = [0u8; 32];
    private_key.copy_from_slice(&material[..32]);
    chain_code.copy_from_slice(&material[32..]);
    material.as_mut_slice().zeroize();
    seed.zeroize();
    for index in [44u32, 501u32, 0u32, 0u32] {
        let mut mac = <HmacSha512 as Mac>::new_from_slice(&chain_code).map_err(|_| "Key derivation unavailable")?;
        let mut data = [0u8; 37];
        data[1..33].copy_from_slice(&private_key);
        data[33..].copy_from_slice(&(index | 0x8000_0000u32).to_be_bytes());
        mac.update(&data);
        data.zeroize();
        let mut derived = mac.finalize().into_bytes();
        private_key.copy_from_slice(&derived[..32]);
        chain_code.copy_from_slice(&derived[32..]);
        derived.as_mut_slice().zeroize();
    }
    let signing_key = SigningKey::from_bytes(&private_key);
    let address = bs58::encode(signing_key.verifying_key().to_bytes()).into_string();
    private_key.zeroize();
    chain_code.zeroize();
    Ok(address)
}
fn encryption_key(password: &str, salt: &[u8]) -> Result<[u8; 32], String> {
    if password.chars().count() < 12 {
        return Err("Wallet encryption password must contain at least 12 characters".into());
    }
    let params = Params::new(65536, 3, 1, Some(32)).map_err(|_| "KDF configuration error")?;
    let kdf = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);
    let mut key = [0u8; 32];
    kdf.hash_password_into(password.as_bytes(), salt, &mut key).map_err(|_| "Unable to derive wallet key")?;
    Ok(key)
}
fn seal(vault_path: &str, password: &str, phrase: &str) -> Result<String, String> {
    if Path::new(vault_path).exists() {
        return Err("Wallet already exists. Refusing to overwrite existing keys".into());
    }
    let phrase = Mnemonic::parse_in(Language::English, phrase).map_err(|_| "Invalid BIP39 English recovery phrase or checksum")?;
    let canonical = phrase.to_string();
    let address = derived_public_key(&canonical)?;
    let mut salt = [0u8; 16];
    let mut nonce = [0u8; 12];
    OsRng.fill_bytes(&mut salt);
    OsRng.fill_bytes(&mut nonce);
    let mut key = encryption_key(password, &salt)?;
    let cipher = Aes256Gcm::new_from_slice(&key).map_err(|_| "Encryption unavailable")?;
    let ciphertext = cipher.encrypt(Nonce::from_slice(&nonce), Payload { msg: canonical.as_bytes(), aad: address.as_bytes() })
        .map_err(|_| "Unable to encrypt wallet")?;
    key.zeroize();
    let vault = Vault {
        version: 1, network: "solana-devnet".into(), derivation: DERIVATION.into(), address: address.clone(),
        salt_hex: hex::encode(salt), nonce_hex: hex::encode(nonce), ciphertext_hex: hex::encode(ciphertext),
    };
    let data = serde_json::to_vec_pretty(&vault).map_err(|_| "Wallet serialization error")?;
    let mut file = OpenOptions::new().write(true).create_new(true).open(vault_path)
        .map_err(|_| "Cannot create wallet file; choose a new name")?;
    file.write_all(&data).map_err(|_| "Unable to save encrypted wallet file")?;
    file.sync_all().map_err(|_| "Unable to sync wallet file")?;
    Ok(address)
}
fn open_vault(vault_path: &str, password: &str) -> Result<(String, String), String> {
    let mut data = String::new();
    File::open(vault_path).map_err(|_| "Wallet file not found")?
        .take(32_768).read_to_string(&mut data).map_err(|_| "Cannot read wallet file")?;
    let vault: Vault = serde_json::from_str(&data).map_err(|_| "Invalid wallet file")?;
    if vault.version != 1 || vault.network != "solana-devnet" || vault.derivation != DERIVATION {
        return Err("Unsupported wallet version, network or derivation".into());
    }
    let salt = hex::decode(vault.salt_hex).map_err(|_| "Invalid wallet salt")?;
    let nonce = hex::decode(vault.nonce_hex).map_err(|_| "Invalid wallet nonce")?;
    let ciphertext = hex::decode(vault.ciphertext_hex).map_err(|_| "Invalid wallet ciphertext")?;
    if salt.len() != 16 || nonce.len() != 12 || ciphertext.len() > 4096 {
        return Err("Invalid wallet structure".into());
    }
    let mut key = encryption_key(password, &salt)?;
    let cipher = Aes256Gcm::new_from_slice(&key).map_err(|_| "Decryption unavailable")?;
    let mut plain = cipher.decrypt(Nonce::from_slice(&nonce), Payload { msg: &ciphertext, aad: vault.address.as_bytes() })
        .map_err(|_| "Incorrect password or damaged encrypted wallet")?;
    key.zeroize();
    let mnemonic = std::str::from_utf8(&plain).map_err(|_| "Invalid recovery phrase encoding")?;
    let address = derived_public_key(mnemonic)?;
    if address != vault.address {
        plain.zeroize();
        return Err("Encrypted wallet address verification failed".into());
    }
    let words = mnemonic.to_string();
    plain.zeroize();
    Ok((address, words))
}
fn run(request: Request) -> Result<Reply, String> {
    if request.vault_path.trim().is_empty() {
        return Err("Wallet path required".into());
    }
    let password = request.password.as_deref().unwrap_or("");
    match request.op.as_str() {
        "create" => {
            let mnemonic = Mnemonic::generate_in(Language::English, 12).map_err(|_| "Wallet randomness unavailable")?;
            let phrase = mnemonic.to_string();
            let address = seal(&request.vault_path, password, &phrase)?;
            Ok(reply(address, Some(phrase)))
        }
        "restore" => {
            let phrase = request.mnemonic.ok_or("Recovery phrase required")?;
            let address = seal(&request.vault_path, password, &phrase)?;
            Ok(reply(address, None))
        }
        "unlock" => {
            let (address, mut words) = open_vault(&request.vault_path, password)?;
            words.zeroize();
            Ok(reply(address, None))
        }
        "reveal" => {
            let (address, words) = open_vault(&request.vault_path, password)?;
            Ok(reply(address, Some(words)))
        }
        _ => Err("Unsupported wallet operation".into()),
    }
}
fn main() {
    let result = std::panic::catch_unwind(|| {
        let mut input = String::new();
        match std::io::stdin().take(32_768).read_to_string(&mut input) {
            Ok(_) => match serde_json::from_str::<Request>(&input) {
                Ok(request) => run(request).unwrap_or_else(error),
                Err(_) => error("Invalid wallet request"),
            },
            Err(_) => error("Unable to read wallet request"),
        }
    }).unwrap_or_else(|_| error("Wallet operation failed"));
    let _ = serde_json::to_writer(std::io::stdout(), &result);
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn known_mnemonic_derivation_stable_and_distinct() {
        let phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
        let address = derived_public_key(phrase).unwrap();
        assert_eq!(address, derived_public_key(phrase).unwrap());
        assert!(bs58::decode(address).into_vec().unwrap().len() == 32);
        assert!(derived_public_key("not a mnemonic").is_err());
    }
    #[test]
    fn encrypted_roundtrip_and_wrong_password() {
        let mut location = std::env::temp_dir();
        location.push(format!("forgecoin-test-{}.wallet.json", rand::random::<u64>()));
        let path = location.to_string_lossy().to_string();
        let phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about";
        let address = seal(&path, "example-only-password-123", phrase).unwrap();
        assert!(seal(&path, "example-only-password-123", phrase).is_err());
        assert!(open_vault(&path, "different-long-password").is_err());
        let (decoded, recovered) = open_vault(&path, "example-only-password-123").unwrap();
        assert_eq!(address, decoded);
        assert_eq!(recovered, phrase);
        let _ = std::fs::remove_file(path);
    }
}
