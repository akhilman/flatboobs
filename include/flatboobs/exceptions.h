#ifndef FLATBOOBS_EXCEPTIONS_H
#define FLATBOOBS_EXCEPTIONS_H

#include <stdexcept>

namespace flatboobs {

class parser_error : public std::runtime_error {
  using std::runtime_error::runtime_error;
};

class not_implemented_error : public std::exception {
public:
  virtual const char *what() const throw() { return "Not implemented"; }
};

class key_error : public std::runtime_error {
  using std::runtime_error::runtime_error;
};

} // namespace flatboobs

#endif // FLATBOOBS_EXCEPTIONS_H
