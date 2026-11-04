// Native FRG genesis-output ring-member exclusion regression.
// Exercises the same constexpr consensus predicate called for EACH output in
// Blockchain::scan_outputkeys_for_indexes after LMDB output height resolution.
// This does not fabricate a spend, signatures, or unlock a public mainnet.
#include "cryptonote_basic/forgecoin_prelaunch.h"
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <vector>

namespace {
bool all_members_allowed(bool mainnet, const std::vector<std::uint64_t>& heights) {
  for (auto height : heights) {
    // The real consensus scanner evaluates the rule per member before
    // visiting/validating each selected ring output's public key.
    if (!cryptonote::forgecoin_prelaunch::output_allowed(mainnet, height))
      return false;
  }
  return true;
}
}

int main() {
  using cryptonote::forgecoin_prelaunch::output_allowed;
  // This includes the original native genesis coinbase output as returned
  // by local read-only /get_outs, whose recorded creation height is zero.
  static_assert(!output_allowed(true, 0), "FRG genesis output must be prohibited");
  static_assert(output_allowed(true, 1), "First mined block output permitted as ring member");
  static_assert(output_allowed(true, 60), "A mature non-genesis output should not be blocked");
  static_assert(output_allowed(false, 0), "Non-mainnet policy must remain unchanged");

  for (std::size_t ring_size : {1U, 2U, 11U, 16U, 64U, 256U}) {
    std::vector<std::uint64_t> members(ring_size, 120);
    assert(all_members_allowed(true, members));
    // Including a zero-height output as a decoy is just as invalid as
    // trying to spend it: no member of a FRG ring may derive from genesis.
    for (std::size_t index = 0; index != ring_size; ++index) {
      members[index] = 0;
      assert(!all_members_allowed(true, members));
      assert(all_members_allowed(false, members));
      members[index] = 120;
    }
    // Any amount of later output maturity does not alter exclusion.
    members.back() = 0;
    if (ring_size > 1)
      members.front() = 1000000;
    assert(!all_members_allowed(true, members));
  }

  // Mixed member heights must be accepted by this particular predicate
  // (signature, age, ring size and other consensus gates are separate).
  assert(all_members_allowed(true, {1, 2, 16, 60, 92}));
  assert(!all_members_allowed(true, {1, 2, 16, 0, 92}));
  std::cout << "PASS: native FRG genesis member excluded at every ring position" << std::endl;
  return 0;
}
