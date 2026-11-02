// ForgeCoin prelaunch consensus restrictions. No runtime or manifest override.
#pragma once
#include <cstdint>
namespace cryptonote { namespace forgecoin_prelaunch {
constexpr bool mining_allowed(bool mainnet) { return !mainnet; }
constexpr bool block_allowed(bool mainnet, std::uint64_t height) {
  return !mainnet || height == 0;
}
// Permanent mainnet rule, separate from the temporary launch lock: genesis
// outputs cannot appear in a spending ring, regardless of maturity or keys.
constexpr bool output_allowed(bool mainnet, std::uint64_t creation_height) {
  return !mainnet || creation_height != 0;
}
} }
