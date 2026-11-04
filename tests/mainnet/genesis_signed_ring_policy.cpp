// Native cryptographic regression using the REAL frozen genesis public output.
//
// The public key is parsed from config/mainnet.identity.json's serialized
// genesis coinbase by tools/extract_frozen_genesis_output_key.py.
// It participates as a decoy in otherwise VALID genuine ring signatures.
// The validator's per-member genesis-height rule must still deny the ring.
//
// This is NOT a signed transaction submitted to a native daemon, nor proof
// of a real genesis spend. The real genesis secret is never available.
#include "crypto/crypto.h"
#include "cryptonote_basic/forgecoin_prelaunch.h"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

int decode_nibble(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  return -1;
}

crypto::public_key parse_public_genesis_key(const std::string &hex) {
  require(hex.size() == 64, "frozen genesis output key must be 32 bytes");
  unsigned char bytes[32] = {0};
  for (std::size_t i = 0; i < 32; ++i) {
    const int hi = decode_nibble(hex[2 * i]);
    const int lo = decode_nibble(hex[2 * i + 1]);
    require(hi >= 0 && lo >= 0, "frozen genesis output key is not hex");
    bytes[i] = static_cast<unsigned char>((hi << 4) | lo);
  }
  crypto::public_key result;
  std::memcpy(&result, bytes, sizeof(bytes));
  require(crypto::check_key(result), "real frozen genesis output key is not curve-valid");
  return result;
}

bool ring_eligible(bool mainnet,
                   const std::vector<std::uint64_t> &member_creation_heights) {
  // Same production predicate evaluated for EVERY resolved output, before
  // Blockchain::scan_outputkeys_for_indexes calls the signature visitor.
  for (const auto height : member_creation_heights)
    if (!cryptonote::forgecoin_prelaunch::output_allowed(mainnet, height))
      return false;
  return true;
}

void test_real_genesis_decoy(std::size_t ring_size,
                            const crypto::public_key &genesis_output) {
  require(ring_size >= 2, "ring must contain non-genesis signer");
  std::vector<crypto::public_key> keys(ring_size);
  std::vector<crypto::secret_key> disposable_secrets(ring_size);
  for (std::size_t i = 0; i < ring_size; ++i) {
    crypto::generate_keys(keys[i], disposable_secrets[i]);
    require(crypto::check_key(keys[i]), "generated native key is invalid");
  }
  const crypto::hash prefix = crypto::rand<crypto::hash>();
  std::vector<crypto::public_key const *> members;
  members.reserve(ring_size);
  for (const auto &pub : keys) members.push_back(&pub);
  std::vector<crypto::signature> signatures(ring_size);
  std::vector<std::uint64_t> member_heights(ring_size, 130);
  require(ring_eligible(true, member_heights), "mature all-mined control was denied");

  for (std::size_t index = 0; index < ring_size; ++index) {
    // The actual network genesis output is inserted as a *decoy*. The real
    // signing key is always a DIFFERENT disposable output; no genesis secret
    // is asserted, assumed, recovered or generated.
    const auto original_key = keys[index];
    keys[index] = genesis_output;
    const std::size_t real_signer = (index + 1) % ring_size;
    crypto::key_image image;
    crypto::generate_key_image(keys[real_signer],
                               disposable_secrets[real_signer], image);
    crypto::generate_ring_signature(prefix, image, members,
                                    disposable_secrets[real_signer],
                                    real_signer, signatures.data());
    require(crypto::check_ring_signature(prefix, image, members,
                                          signatures.data()),
            "VALID ring including real genesis public decoy failed crypto verification");

    member_heights[index] = 0;
    require(!ring_eligible(true, member_heights),
            "mainnet allowed a cryptographically valid ring with genesis output");
    require(ring_eligible(false, member_heights),
            "test FAKECHAIN unnecessarily forbids the genesis ring decoy");

    crypto::hash wrong_prefix = prefix;
    wrong_prefix.data[0] ^= 1;
    require(!crypto::check_ring_signature(wrong_prefix, image, members,
                                           signatures.data()),
            "invalid signed-ring message was cryptographically accepted");
    member_heights[index] = 130;
    keys[index] = original_key;
  }
  require(ring_eligible(true, member_heights),
          "all-mature mined ring did not recover after removing genesis decoy");
}

} // namespace

int main(int argc, char **argv) {
  try {
    require(argc == 2, "expected only PUBLIC genesis output key argument");
    const auto genesis_output = parse_public_genesis_key(argv[1]);
    for (const auto ring_size : {2U, 11U, 16U, 64U})
      test_real_genesis_decoy(ring_size, genesis_output);
    std::cout << "PASS: real frozen-genesis public key as decoy in "
                 "cryptographically VALID native signed rings, all decoy "
                 "positions rejected by MAINNET member eligibility, "
                 "invalid signature control denied"
              << std::endl;
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "FAIL: native signed genesis-decoy regression: "
              << e.what() << std::endl;
    return 1;
  }
}
