#pragma once

#include <stdexcept>

namespace flatboobs {

// TODO move to header
class ParserError : public std::runtime_error {
  using std::runtime_error::runtime_error;
};

// TODO move to header
class NotImplementedError : public std::exception {
public:
  virtual const char *what() const throw() { return "Not implemented"; }
};

} // namespace flatboobs
