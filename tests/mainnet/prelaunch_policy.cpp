#include "cryptonote_basic/forgecoin_prelaunch.h"
#include <cassert>
#include <initializer_list>
#include <cstdint>
#include <limits>
int main() {
  using namespace cryptonote::forgecoin_prelaunch;
  static_assert(!mining_allowed(true), "Mainnet miner must be locked");
  static_assert(mining_allowed(false), "Separate test networks retain their own policy");
  assert(block_allowed(true, 0));
  for (std::uint64_t h : {std::uint64_t(1), std::uint64_t(16), std::uint64_t(60),
                          std::uint64_t(92), std::numeric_limits<std::uint64_t>::max()}) {
    assert(!block_allowed(true, h));
    assert(block_allowed(false, h));
    assert(output_allowed(true, h));
  }
  assert(!output_allowed(true, 0));
  assert(output_allowed(false, 0));
}
