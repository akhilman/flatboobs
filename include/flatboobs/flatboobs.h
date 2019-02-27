
#pragma once

#include <cstring>
#include <stdexcept>

#include <flatbuffers/flatbuffers.h>

#include <pybind11/buffer_info.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace flatboobs {

using namespace pybind11::literals;
namespace fb = flatbuffers;
namespace py = pybind11;

/*
 * RawData
 */

class RawData {

public:
  RawData() : _data{nullptr}, _size{0}, _offset{0}, _py_object{py::none{}} {}
  explicit RawData(const char *src_data, size_t src_size, size_t src_offset = 0)
      : _size{src_size}, _offset{0}, _py_object{py::none{}} {
    auto ptr = new char[src_size];
    std::memcpy(ptr, src_data + src_offset, _size);
    _data = ptr;
  }
  explicit RawData(const py::bytes &py_bytes)
      : _offset{0}, _py_object{py_bytes} {
    Py_ssize_t src_size;
    char *src_data;
    PYBIND11_BYTES_AS_STRING_AND_SIZE(py_bytes.ptr(), &src_data, &src_size);
    _data = src_data;
    _size = src_size;
  }

  explicit RawData(const RawData &other) {
    RawData(other.data(), other.size());
  }

  RawData &operator=(const RawData &other) = delete;
  RawData &operator=(RawData &&other) = delete;
  ~RawData() { delete[] _data; }

  void steal_from_builder(fb::FlatBufferBuilder &builder) {
    if (_data)
      throw std::logic_error("Data already set");
    _data = reinterpret_cast<const char *>(builder.ReleaseRaw(_size, _offset));
  }

  const char *data() const { return _data; };
  const size_t size() const { return _size; }
  const py::buffer_info buffer() const {
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
  const py::bytes tobytes() const { return py::bytes{data(), size()}; };

private:
  const char *_data;
  size_t _size;
  size_t _offset;
  py::object _py_object;
};
}; // namespace flatboobs
