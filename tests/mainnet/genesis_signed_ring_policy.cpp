// Isolated native ring-signature regression for ForgeCoin's genesis exclusion.
// A cryptographically valid signed ring is still not eligible for MAINNET
// if any one of its on-chain output creation heights equals zero.
// This deliberately does NOT create a wallet transaction, bypass prelaunch,
// or claim a real genesis private key / signed spending witness.
#include "crypto/crypto.h"
#include "cryptonote_basic/forgecoin_prelaunch.h"

#include <cstddef>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
void require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

bool consensus_ring_eligible(bool mainnet,
                             const std::vector<std::uint64_t> &heights) {
  // Exactly the per-output policy invoked by
  // Blockchain::scan_outputkeys_for_indexes after native LMDB height lookup.
  for (const auto creation_height : heights)
    if (!cryptonote::forgecoin_prelaunch::output_allowed(
            mainnet, creation_height))
      return false;
  return true;
}

void test_signed_ring(std::size_t ring_size) {
  require(ring_size >= 2, "invalid crypto test ring");
  // All keys and the signing secret are disposable, generated in this process.
  // None is the key for the real genesis coinbase.
  std::vector<crypto::public_key> keys(ring_size);
  std::vector<crypto::secret_key> secrets(ring_size);
  std::vector<const crypto::public_key *> ptrs;
  ptrs.reserve(ring_size);
  for (std::size_t i = 0; i < ring_size; ++i) {
    crypto::generate_keys(keys[i], secrets[i]);
    require(crypto::check_key(keys[i]), "invalid generated native public key");
    ptrs.push_back(&keys[i]);
  }
  const std::size_t real = ring_size / 2;
  const crypto::hash message = crypto::rand<crypto::hash>();
  crypto::key_image image;
  crypto::generate_key_image(keys[real], secrets[real], image);
  std::vector<crypto::signature> signatures(ring_size);
  crypto::generate_ring_signature(message, image, ptrs,
                                  secrets[real], real, signatures.data());
  require(crypto::check_ring_signature(message, image, ptrs, signatures.data()),
          "native cryptographic signed-ring control is invalid");

  std::vector<std::uint64_t> heights(ring_size, 130);
  require(consensus_ring_eligible(true, heights),
          "valid mature mined-height ring unexpectedly prohibited");
  require(consensus_ring_eligible(false, heights),
          "unmodified fakechain must permit the control ring");

  for (std::size_t genesis_position = 0; genesis_position < ring_size;
       ++genesis_position) {
    // Tag ONE otherwise validly signed member as creation height zero,
    // independently of where the genuine signer sits. This models a decoy
    // reference to the REAL genesis output and checks member-level policy.
    heights[genesis_position] = 0;
    require(crypto::check_ring_signature(message, image, ptrs,
                                          signatures.data()),
            "cryptographic ring validity changed with metadata only");
    require(!consensus_ring_eligible(true, heights),
            "mainnet ring accepted a height-zero (genesis) member");
    require(consensus_ring_eligible(false, heights),
            "test-only fakechain consensus should be unaffected");
    heights[genesis_position] = 130;
  }

  crypto::hash wrong_message = message;
  wrong_message.data[0] ^= 1;
  require(!crypto::check_ring_signature(wrong_message, image, ptrs,
                                        signatures.data()),
          "negative signature control accepted wrong message");
}

} // namespace

int main() {
  try {
    for (const auto ring_size : {2U, 11U, 16U, 64U})
      test_signed_ring(ring_size);
    std::cout << "PASS: genuine native cryptographically valid rings, "
                 "all height-zero member positions denied by "
                 "mainnet output eligibility; negative signature control"
              << std::endl;
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "FAIL: native genesis signed-ring regression: "
              << e.what() << std::endl;
    return 1;
  }
}
