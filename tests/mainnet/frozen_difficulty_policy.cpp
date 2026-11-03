// Regression tests for actual frozen FRG consensus difficulty logic.
// Must compile/link header's real inline functions; no daemon or mining.
#include "cryptonote_basic/forgecoin_difficulty.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <vector>

namespace cryptonote {
// Standalone sentinel for the pre-existing non-mainnet algorithm.
// Production non-mainnet implementation is not changed or linked by this test.
difficulty_type next_difficulty(std::vector<std::uint64_t>,
                                std::vector<difficulty_type>,
                                std::size_t) {
    return difficulty_type(777);
}
}

using cryptonote::difficulty_type;
using cryptonote::next_forgecoin_difficulty;
using cryptonote::forgecoin_lwma_window;

static void history(std::size_t ancestor_count, std::uint64_t spacing,
                    std::vector<std::uint64_t>& times,
                    std::vector<difficulty_type>& work) {
    times.clear();
    work.clear();
    for (std::size_t i = 0; i < ancestor_count; ++i) {
        times.push_back(1793000000ULL + i * spacing);
        work.push_back(difficulty_type(1) + difficulty_type(i) * 500000);
    }
}

int main() {
    static_assert(cryptonote::FORGE_LWMA_HEIGHT == 16, "Changed consensus activation");
    static_assert(cryptonote::FORGE_LWMA_WINDOW == 90, "Changed consensus window");
    static_assert(cryptonote::FORGE_STARTUP_FIXED_LAST_HEIGHT == 15, "Changed startup range");
    static_assert(cryptonote::FORGE_STARTUP_INITIAL_DIFFICULTY == 500000, "Changed start difficulty");
    static_assert(cryptonote::FORGE_MINIMUM_DIFFICULTY == 400000, "Changed minimum");

    std::vector<std::uint64_t> t;
    std::vector<difficulty_type> c;

    // Through height 15, difficulty must be constant even with no history.
    for (std::uint64_t h = 1; h <= 15; ++h) {
        assert(next_forgecoin_difficulty({}, {}, 120, h, true) == 500000);
    }
    assert(next_forgecoin_difficulty({}, {}, 120, 0, true) == 0);
    assert(next_forgecoin_difficulty({}, {}, 60, 1, true) == 0);

    // Activation: 16 ancestor blocks (genesis + heights 1..15), 15 intervals.
    history(16, 120, t, c);
    assert(next_forgecoin_difficulty(t, c, 120, 16, true) == 495000);

    // Native rule is 0.99 bias on 120-second solve time; verify continuity
    // at startup activation, full 90-interval window, and height 92.
    for (std::uint64_t h : {17ULL, 32ULL, 90ULL, 91ULL, 92ULL, 150ULL}) {
        history(h, 120, t, c);
        assert(next_forgecoin_difficulty(t, c, 120, h, true) == 495000);
    }

    history(91, 30, t, c);
    assert(next_forgecoin_difficulty(t, c, 120, 91, true) == 1980000);
    history(91, 480, t, c);
    assert(next_forgecoin_difficulty(t, c, 120, 91, true) == 400000);

    // Stale or truncated history fails closed; not silently a smaller LWMA.
    history(15, 120, t, c);
    assert(next_forgecoin_difficulty(t, c, 120, 16, true) == 0);
    history(91, 120, t, c);
    auto less = c;
    less.pop_back();
    assert(next_forgecoin_difficulty(t, less, 120, 91, true) == 0);
    assert(next_forgecoin_difficulty(t, c, 60, 91, true) == 0);
    assert(forgecoin_lwma_window(t, c, 120, 0) == 0);
    assert(forgecoin_lwma_window(t, c, 120, 91) == 0);
    c[70] = c[69]; // equal cumulative difficulty is invalid
    assert(next_forgecoin_difficulty(t, c, 120, 91, true) == 0);

    // Consensus normalizes a descending timestamp rather than allowing
    // non-positive solve intervals or a divide-by-zero.
    history(91, 120, t, c);
    t[45] = t[44] - 10;
    assert(next_forgecoin_difficulty(t, c, 120, 91, true) > 0);

    // An unrepresentable ancestor timestamp fails closed.
    t[0] = std::numeric_limits<std::uint64_t>::max();
    assert(next_forgecoin_difficulty(t, c, 120, 91, true) == 0);

    // Existing testnet/stagenet difficulty selector remains unchanged.
    assert(next_forgecoin_difficulty({}, {}, 120, 16, false) == 777);
    std::cout << "PASS: FRG real header startup/LWMA16/90/floor/invalid-history regressions" << std::endl;
    return 0;
}
