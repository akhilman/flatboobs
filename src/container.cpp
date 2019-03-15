#include <flatboobs/container.h>

namespace flatboobs {

namespace fb = flatbuffers;
namespace py = pybind11;

Bytes::Bytes() : _data{nullptr}, _size{0}, _offset{0}, _data_holder{} {}
// Bytes::Bytes(const Bytes &other, const size_t size, const size_t offset) {
//   if (offset + size > other._size)
//     throw std::out_of_range("Data out of range");
//   _data = other._data;
//   _offset = other._offset + offset;
//   _size = size;
// }
// Bytes &operator=(const Bytes &other);

Bytes::Bytes(const py::bytes py_bytes) : _offset{0} {
  Py_ssize_t src_size;
  char *src_data;
  PYBIND11_BYTES_AS_STRING_AND_SIZE(py_bytes.ptr(), &src_data, &src_size);
  _data = src_data;
  _size = src_size;
  _data_holder = py_bytes;
}
Bytes::Bytes(const py::bytes py_bytes, const size_t size, const size_t offset)
    : _size{size}, _offset{offset} {
  Py_ssize_t src_size;
  char *src_data;
  PYBIND11_BYTES_AS_STRING_AND_SIZE(py_bytes.ptr(), &src_data, &src_size);
  if (_size + _offset > src_size)
    throw std::out_of_range("Data out of range");
  _data = src_data;
  _data_holder = py_bytes;
}
Bytes::Bytes(py::buffer &buffer) : _offset{0} {
  py::buffer_info info = buffer.request();
  _size = info.itemsize * info.size;
  char *data = new char[_size];
  std::memcpy(data, info.ptr, _size);
  _data = const_cast<const char *>(data);
  _data_holder = std::unique_ptr<const char>(data);
  // py::print("buffer:", info.format, info.itemsize, info.size, info.ndim,
  //           info.shape, info.strides);
}

Bytes::Bytes(fb::FlatBufferBuilder &builder) {
  _data = reinterpret_cast<const char *>(builder.ReleaseRaw(_size, _offset));
  _data_holder = std::unique_ptr<const char>(_data);
}
const Bytes Bytes::take_from_builder(fb::FlatBufferBuilder &builder) {
  return Bytes(builder);
}

const char *Bytes::data() const { return _data + _offset; };
const size_t Bytes::size() const { return _size; }
const py::buffer_info Bytes::buffer() const {
  // TODO make buffer readonly
  // https://github.com/pybind/pybind11/pull/1466
  py::buffer_info info{const_cast<char *>(data()),
                       sizeof(char),
                       py::format_descriptor<char>::format(),
                       1,
                       {size()},
                       {sizeof(char)}};
  return info;
}
const py::bytes Bytes::tobytes() const {
  if (std::holds_alternative<py::bytes>(_data_holder))
    return std::get<py::bytes>(_data_holder);
  return py::bytes{data(), size()};
}

} // namespace flatboobs
