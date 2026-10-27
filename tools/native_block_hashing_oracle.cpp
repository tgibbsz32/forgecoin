// Offline CryptoNote serialization oracle for a trusted disposable block template.
// No daemon RPC, wallet, mining or network access. Never built for normal releases.
#include <cstdint>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>
#include "cryptonote_basic/cryptonote_format_utils.h"

namespace {
unsigned hex_digit(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  throw std::runtime_error("non-hexadecimal block byte");
}
std::string from_hex(const std::string &hex) {
  if (hex.empty() || hex.size() > 524288 || (hex.size() % 2) != 0)
    throw std::runtime_error("invalid or oversized block hex");
  std::string data;
  data.reserve(hex.size() / 2);
  for (size_t i = 0; i < hex.size(); i += 2)
    data.push_back(static_cast<char>((hex_digit(hex[i]) << 4) | hex_digit(hex[i + 1])));
  return data;
}
std::string to_hex(const std::string &bytes) {
  static constexpr char digits[] = "0123456789abcdef";
  std::string out;
  out.reserve(bytes.size() * 2);
  for (const auto c : bytes) {
    const unsigned byte = static_cast<unsigned char>(c);
    out.push_back(digits[byte >> 4]);
    out.push_back(digits[byte & 15]);
  }
  return out;
}
}

int main() {
  try {
    std::string input;
    if (!std::getline(std::cin, input))
      throw std::runtime_error("missing serialized block");
    const cryptonote::blobdata full = from_hex(input);
    cryptonote::block block;
    if (!cryptonote::parse_and_validate_block_from_blob(
            cryptonote::blobdata_ref(full), block))
      throw std::runtime_error("native block parser rejected candidate");
    const cryptonote::blobdata canonical = cryptonote::block_to_blob(block);
    if (canonical != full)
      throw std::runtime_error("candidate is not canonical serialized block");
    const cryptonote::blobdata hashing = cryptonote::get_block_hashing_blob(block);
    if (hashing.size() < 40 || hashing.size() > 262144)
      throw std::runtime_error("invalid native hashing blob size");
    std::cout << to_hex(canonical) << '\n' << to_hex(hashing) << '\n';
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "native candidate rejected: " << e.what() << '\n';
    return 1;
  }
}
