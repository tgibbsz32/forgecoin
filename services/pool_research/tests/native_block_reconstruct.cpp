// Isolated research only. Reconstruct a complete block after a fixed-width
// miner-transaction extra reservation changes, using native consensus hashing.
// No sockets, daemon RPC, wallets, block submission, or mining here.
#include "cryptonote_basic/cryptonote_format_utils.h"
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {
unsigned nibble(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  throw std::runtime_error("invalid hex");
}
std::string decode(const std::string& hex) {
  if (hex.empty() || hex.size() % 2 || hex.size() > 524288)
    throw std::runtime_error("invalid hex length");
  std::string result;
  result.reserve(hex.size() / 2);
  for (size_t i = 0; i < hex.size(); i += 2)
    result.push_back(char(nibble(hex[i]) * 16 + nibble(hex[i + 1])));
  return result;
}
std::string encode(const std::string& bytes) {
  static constexpr char digits[] = "0123456789abcdef";
  std::string result;
  result.reserve(bytes.size() * 2);
  for (unsigned char c : bytes) {
    result.push_back(digits[c >> 4]);
    result.push_back(digits[c & 15]);
  }
  return result;
}
std::string read_line(std::ifstream& input) {
  std::string line;
  if (!std::getline(input, line) || line.size() > 524288)
    throw std::runtime_error("missing or oversized input");
  if (!line.empty() && line.back() == '\r') line.pop_back();
  return line;
}
} // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 2) throw std::runtime_error("usage: native_block_reconstruct INPUT_FILE");
    std::ifstream input(argv[1], std::ios::binary | std::ios::ate);
    if (!input || input.tellg() > 1048576)
      throw std::runtime_error("missing or oversized input file");
    input.seekg(0);
    const std::string original = decode(read_line(input));
    const std::string expected_hashing = decode(read_line(input));
    const std::string offset_text = read_line(input);
    const std::string replacement = decode(read_line(input));
    if (replacement.size() != 8 || offset_text.empty() ||
        offset_text.find_first_not_of("0123456789") != std::string::npos)
      throw std::runtime_error("invalid reserve replacement or offset");
    const unsigned long long parsed = std::stoull(offset_text);
    if (parsed > original.size() || replacement.size() > original.size() - parsed)
      throw std::runtime_error("reserve offset out of range");
    const size_t offset = static_cast<size_t>(parsed);
    std::string trailing;
    if (std::getline(input, trailing) && !trailing.empty())
      throw std::runtime_error("unexpected trailing data");

    cryptonote::block block;
    if (!cryptonote::parse_and_validate_block_from_blob(
          cryptonote::blobdata_ref(original), block))
      throw std::runtime_error("cannot parse native block");
    if (cryptonote::block_to_blob(block) != original ||
        cryptonote::get_block_hashing_blob(block) != expected_hashing)
      throw std::runtime_error("daemon template does not match native consensus");

    // Locate the exact miner tx extra serialization, not an arbitrary byte match.
    const auto& extra = block.miner_tx.extra;
    if (extra.size() < replacement.size())
      throw std::runtime_error("miner tx extra too short");
    const std::string extra_bytes(extra.begin(), extra.end());
    const size_t start = original.find(extra_bytes);
    if (start == std::string::npos ||
        original.find(extra_bytes, start + 1) != std::string::npos ||
        offset < start || offset - start > extra.size() - replacement.size())
      throw std::runtime_error("reserved bytes not uniquely inside miner tx extra");

    const size_t relative = offset - start;
    if (original.compare(offset, replacement.size(), replacement) == 0)
      throw std::runtime_error("reserve replacement did not change template");
    std::copy(replacement.begin(), replacement.end(), block.miner_tx.extra.begin() + relative);
    block.miner_tx.invalidate_hashes();
    block.invalidate_hashes();
    const std::string rebuilt = cryptonote::block_to_blob(block);
    std::string patched = original;
    patched.replace(offset, replacement.size(), replacement);
    if (rebuilt != patched)
      throw std::runtime_error("native serialization modified unexpected bytes");
    const std::string hashing = cryptonote::get_block_hashing_blob(block);
    if (hashing == expected_hashing)
      throw std::runtime_error("tree root did not change after reserve modification");
    const std::string header = cryptonote::t_serializable_object_to_blob(
        static_cast<cryptonote::block_header>(block));
    if (header.size() < 39 || hashing.size() != expected_hashing.size() ||
        hashing.compare(0, header.size(), expected_hashing, 0, header.size()) != 0)
      throw std::runtime_error("candidate header unexpectedly changed");
    std::cout << "FULL " << encode(rebuilt) << "\n"
              << "HASHING " << encode(hashing) << "\n"
              << "OFFSET " << offset << "\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "REJECT: " << error.what() << "\n";
    return 1;
  }
}
