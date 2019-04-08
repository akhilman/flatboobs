#ifndef FLATBOOBS_UTILS_HPP
#define FLATBOOBS_UTILS_HPP

#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>

namespace flatboobs {

inline std::string escape_string(const std::string src) {
  std::stringstream ret;
  for (unsigned char c : src)
    if (c == '\\')
      ret << "\\\\";
    else if (c >= 0x20 && c <= 0x7E)
      ret << c;
    else
      ret << "\\x" << std::setfill('0') << std::setw(2) << std::hex << (int)c;
  return ret.str();
}

inline std::string unescape_string(const std::string src) {
  std::stringstream ret;
  auto src_length = src.length();
  decltype(src_length) i = 0;
  char hex_str[] = "\0\0\0";
  char *p;
  while (i < src_length) {
    if (src[i] == '\\') {
      i++;
      if (src[i] == '\\')
        ret << '\\';
      else if (src[i] == 'x') {
        p = nullptr;
        if (i + 2 < src_length) {
          hex_str[0] = src[++i];
          hex_str[1] = src[++i];
          ret << (unsigned char)std::strtol(hex_str, &p, 16);
        }
        if (p != hex_str + 2)
          throw std::runtime_error("malformated hex value");
      }
    } else
      ret << src[i];
    i++;
  }
  return ret.str();
}

std::ostream &hexdump(std::ostream &stream, const std::string_view _data) {

  stream << std::hex << std::setfill('0');

  auto begin = _data.begin();
  auto end = _data.end();

  int address = 0;
  for (auto row = begin; row < end; row += 16) {

    auto last = row + 16;
    if (last > end)
      last = end;

    // Show the address
    stream << std::setw(8) << address;
    address += 16;

    // Show the hex codes
    for (auto i = 0; i < 16; i++) {
      if (i % 8 == 0)
        stream << ' ';
      if (row + i < end)
        stream << ' ' << std::setw(2) << (unsigned)(uint8_t)row[i];
      else
        stream << "   ";
    }

    // Show printable characters
    stream << "  ";
    for (auto i = 0; i < 16; i++) {
      if (row + i >= end)
        break;
      if (int(row[i]) < 32)
        stream << '.';
      else
        stream << (char)row[i];
    }

    stream << "\n";
  }
  return stream;
}

} // namespace flatboobs

#endif // FLATBOOBS_UTILS_HPP
