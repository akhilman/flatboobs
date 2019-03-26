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

} // namespace flatboobs

#endif // FLATBOOBS_UTILS_HPP
