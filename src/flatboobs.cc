
#include <flatboobs/container.h>

namespace flatboobs {

using namespace pybind11::literals;
namespace fb = flatbuffers;
namespace py = pybind11;

void pydefine_Bytes(py::module &m) {
  py::class_<Bytes, std::shared_ptr<Bytes>>(m, "Bytes", py::buffer_protocol())
      .def(py::init<>())
      // .def(py::init<const Bytes &>())
      // .def(py::init<const Bytes &, size_t, size_t>(), "other"_a, "size"_a,
      //      "offset"_a = 0)
      .def(py::init<const py::bytes &>())
      .def(py::init<const py::bytes &, size_t, size_t>(), "bytes"_a, "size"_a,
           "offset"_a = 0)
      .def(py::init<py::buffer &>())
      .def_buffer(&Bytes::buffer)
      .def("__len__", &Bytes::size)
      .def("tobytes", &Bytes::tobytes);
}

PYBIND11_MODULE(flatboobs, m) {

  m.doc() = "Base classes and tools for all generated objects";

  py::module::import("flatboobs.idl");

  pydefine_Bytes(m);
}

} // namespace flatboobs
