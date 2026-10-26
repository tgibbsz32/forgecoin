#pragma once
#include <algorithm>
#include <cstdint>
#include <limits>
#include <vector>
#include "difficulty.h"

namespace cryptonote {
// Fresh mainnet consensus, cloned from validated 20261020 candidate.
constexpr std::uint64_t FORGE_DIFFICULTY_FLOOR_HEIGHT = 1;
constexpr std::uint64_t FORGE_MINIMUM_DIFFICULTY = 400000;
constexpr std::uint64_t FORGE_DIFFICULTY_MILLION_HEIGHT = 1;
constexpr std::uint64_t FORGE_MINIMUM_DIFFICULTY_MILLION = 400000;
constexpr std::uint64_t FORGE_LWMA_HEIGHT = 16;
constexpr std::uint64_t FORGE_STARTUP_FIXED_LAST_HEIGHT = 15;
constexpr std::uint64_t FORGE_STARTUP_INITIAL_DIFFICULTY = 500000;
constexpr std::size_t FORGE_LWMA_WINDOW = 90;
constexpr std::uint8_t FORGE_LWMA_VERSION = 19;
constexpr std::size_t FORGE_LWMA_TIMESTAMP_WINDOW = 11;
constexpr std::uint64_t FORGE_LWMA_FUTURE_LIMIT = FORGE_LWMA_WINDOW * 120 / 20;

template<typename Difficulty>
Difficulty apply_forgecoin_difficulty_floor(Difficulty calculated, std::uint64_t, bool mainnet)
{
  if (mainnet && calculated != 0 && calculated < FORGE_MINIMUM_DIFFICULTY)
    return Difficulty(FORGE_MINIMUM_DIFFICULTY);
  return calculated;
}

// Integer LWMA for N intervals. N=90 reproduces the existing v19 rule.
// For startup, N grows with available ancestor intervals.
// No new block's timestamp is used to determine its own required difficulty.
inline difficulty_type forgecoin_lwma_window(
    const std::vector<std::uint64_t>& timestamps,
    const std::vector<difficulty_type>& cumulative,
    std::uint64_t target, std::size_t n)
{
  if (timestamps.size() != cumulative.size() || n == 0 ||
      n > FORGE_LWMA_WINDOW || timestamps.size() < n + 1 || target != 120)
    return 0;
  const std::size_t start = timestamps.size() - n - 1;
  std::uint64_t previous = timestamps[start];
  std::uint64_t weighted = 0;
  for (std::size_t i=1; i<=n; ++i)
  {
    if (cumulative[start+i] <= cumulative[start+i-1] ||
        previous == std::numeric_limits<std::uint64_t>::max())
      return 0;
    const std::uint64_t current = std::max(timestamps[start+i], previous+1);
    weighted += i * std::min(std::uint64_t(6)*target, current-previous);
    previous = current;
  }
  weighted = std::max(weighted, std::uint64_t(n)*n*target/20);
  const boost::multiprecision::uint256_t work = cumulative.back()-cumulative[start];
  const boost::multiprecision::uint256_t result = work*target*(n+1)*99/(200*weighted);
  if (result > std::numeric_limits<difficulty_type>::max())
    return 0;
  return std::max(difficulty_type(1), result.convert_to<difficulty_type>());
}

inline difficulty_type forgecoin_lwma(
    const std::vector<std::uint64_t>& timestamps,
    const std::vector<difficulty_type>& cumulative, std::uint64_t target)
{
  return forgecoin_lwma_window(timestamps, cumulative, target, FORGE_LWMA_WINDOW);
}

inline difficulty_type next_forgecoin_difficulty(
    const std::vector<std::uint64_t>& timestamps,
    const std::vector<difficulty_type>& cumulative, std::uint64_t target,
    std::uint64_t height, bool mainnet)
{
  if (!mainnet)
    return next_difficulty(timestamps, cumulative, target);
  if (target != 120 || height == 0) return 0;
  if (height <= FORGE_STARTUP_FIXED_LAST_HEIGHT)
    return difficulty_type(FORGE_STARTUP_INITIAL_DIFFICULTY);
  if (timestamps.size() != cumulative.size() || timestamps.size() < 2)
    return 0;
  const std::size_t n = static_cast<std::size_t>(std::min<std::uint64_t>(FORGE_LWMA_WINDOW, height-1));
  // Missing ancestors must fail closed, never silently select a different window.
  if (timestamps.size() < n + 1) return 0;
  return apply_forgecoin_difficulty_floor(
      forgecoin_lwma_window(timestamps, cumulative, target, n), height, true);
}
}
