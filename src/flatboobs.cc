
#include <flatboobs/flatboobs.h>

namespace flatboobs {

using namespace pybind11::literals;
namespace fb = flatbuffers;
namespace py = pybind11;

PYBIND11_MODULE(flatboobs, m) {
  m.doc() = "Raw binary data.";
  py::class_<RawData>(m, "RawData").def(py::init<>());
}

} // namespace flatboobs
