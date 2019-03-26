#ifndef FLATBOOBS_CONTAINER_HPP
#define FLATBOOBS_CONTAINER_HPP

#include <stdexcept>
#include <variant>

#include <flatbuffers/flatbuffers.h>
#include <flatbuffers/idl.h>

#include <flatboobs/exceptions.hpp>
#include <pybind11/buffer_info.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace flatboobs {

namespace fb = flatbuffers;
namespace py = pybind11;

/*
 * IMessage
 */

class IMessage {
public:
  IMessage() = default;
  IMessage(const IMessage &) = delete;
  IMessage &operator=(const IMessage &) = delete;
  virtual ~IMessage() = default;
  virtual const char *data() const = 0;
  virtual const size_t size() const = 0;
  operator const char *() { return (const char *)data(); }
};

template <typename T> class LazyBufMessage : public IMessage {
public:
  using flatbuf_type = typename T::flatbuf_type;

  LazyBufMessage() : size_{0}, offset_{0}, data_{nullptr} {}
  virtual ~LazyBufMessage() = default;

  virtual const char *data() const { return data_.get() + offset_; }
  virtual const size_t size() const { return size_; }

private:
  friend T;
  void steal_from_builder(flatbuffers::FlatBufferBuilder &&builder) {
    size_ = builder.GetSize();
    size_t buffer_size; // total buffer size with usless padding.
    const char *data = reinterpret_cast<const char *>(
        builder.ReleaseRaw(buffer_size, offset_));
    data_ = std::unique_ptr<const char>(data);
  };
  size_t size_;
  size_t offset_;
  std::unique_ptr<const char> data_;
}; // namespace flatboobs

/*
 * Bytes
 */

// TODO use std::string_view and std::copy
// TODO rename to ByteMessage

class Bytes : public IMessage {

  // TODO BYTES variant not used, use it or drop it
  using holder_t = std::variant<std::monostate, std::shared_ptr<const Bytes>,
                                py::bytes, std::unique_ptr<const char>>;
  enum class HolderType { NONE, BYTES, PYBYTES, PTRCHAR };

private:
  Bytes(fb::FlatBufferBuilder &builder);

public:
  Bytes();
  // Bytes(const Bytes &other);
  // Bytes(const Bytes &other, const size_t size, const size_t offset = 0);
  // Bytes &operator=(const Bytes &other);

  Bytes(const py::bytes py_bytes);
  Bytes(const py::bytes py_bytes, const size_t size, const size_t offset = 0);
  Bytes(py::buffer &buffer);
  static const Bytes take_from_builder(fb::FlatBufferBuilder &builder);

  const char *data() const override;
  const size_t size() const override;
  const py::buffer_info buffer() const;
  const py::bytes tobytes() const;

private:
  const char *data_;
  size_t size_;
  size_t offset_;
  holder_t _data_holder;
};

/*
 * Container
 */

class Container {
public:
  virtual ~Container() = default;

  // virtual const std::string fully_qualified_name() const = 0;
  // virtual const std::string name() const = 0;

  // virtual const bool is_evolved() const = 0;
  // virtual const fb::Offset<FBT> build() const;
};

class StructLike : public Container {
public:
  // type const name() const; // getters
  virtual const std::vector<std::string> _keys() const;
  // virtual const VTs _get(const std::string &key) const;

  // evolve
};

/*
class StructLike : public Container {

public:
  struct Fields {
    virtual ~Fields() = default;
    virtual const py::object __get(const std::string &key) const = 0;
  };

  virtual const std::vector<std::string> keys() const = 0;
  virtual const std::vector<py::object> values() const = 0;
  virtual const std::tuple<std::string, py::object> items() const = 0;

  virtual bool contains(const std::string &key) const = 0;
  virtual py::iterator py_iter() const = 0;
  virtual const py::object get(const std::string &key) const = 0;
  virtual const py::object get(const std::string &key,
                               const py::object &default_) const = 0;
  virtual size_t lenght() = 0;
};

class Table : public StructLike {
public:
  struct Fields : public StructLike::Fields {
    using StructLike::Fields::Fields;
  };
};

class Struct : public StructLike {
public:
  struct Fields : public StructLike::Fields {
    using StructLike::Fields::Fields;
  };
  virtual const size_t bytesize() const = 0;
  virtual const std::string format() const = 0;

  virtual const py::buffer_info buffer() const = 0;
};
*/

/*
 * Struct
 */

/*
template <typename RC, typename FC> class Struct : public Container<RC> {
  using container_class = Container<RC>;
  using struct_class = Struct<RC, FC>;
  using fields_class = FC;
  using fbreader_class = RC;
  using value_type = typename fields_class::value_type;

  static_assert(std::is_same<typename FC::fbreader_class, RC>::value);

public:
  Struct();
      : Container<RC>{type_info_, data_, fbreader_}, fields{fields_} {}
      Struct(const TypeInfo *type_info_, std::shared_ptr<const Bytes> data_,
             const fbreader_class *fbreader_,
             std::shared_ptr<const fields_class> fields_)
          : Container<RC>{type_info_, data_, fbreader_}, fields{fields_} {}

      std::shared_ptr<const fields_class> fields;

      bool contains(const std::string &key) const;
      py::iterator py_iter() const;
      const value_type get(const std::string &key) const;
      const value_type get(const std::string &key,
                           const py::object &default_) const;
      const std::vector<const std::string> keys() const;
      const std::vector<const value_type> values() const;

      static size_t lenght();
      static bool is_fixed();

      static std::shared_ptr<const struct_class> evolve(const py::dict &);
      static std::shared_ptr<const struct_class> evolve(const py::tuple &);
      static std::shared_ptr<const struct_class> evolve(py::buffer &);

    protected:
      fb::Offset<fbreader_class>
      build(fbreader_class *fbreader,
            std::map<void *, fb::Offset<void>> offset_map);
};
*/

/*
 * Vector
 */
/*
template <typename CP, typename IC> class Vector : public Container {
  using container_class = Vector<CP, IC>;
  using proto_class = CP;
  using item_calss = IC;
  using fb_class = typename proto_class::fb_class;

public:
  Vector(const Bytes &bytes, size_t offset);

  const bool contains(const item_calss value) const;
  py::iterator py_iter() const;
  const item_calss get(const size_t index) const;
  const item_calss get(const py::slice slice) const;
  const size_t lenght() const;

  py::object asarray();

  static const container_class evolve(const py::list &);
  static const container_class evolve(py::buffer &);

  static const container_class unpackb(const Bytes &, size_t offset);
  static const container_class unpackb(const Bytes &);
  static const container_class unpackb(const py::bytes &);
  static const container_class unpackb(const py::buffer &);

  const Bytes packb();

protected:
  fb::Offset<fb_class> build(fb_class *fbc,
                             std::map<void *, fb::Offset<void>> offset_map);
};
*/

/*
 * Utils
 */

template <typename T>
std::shared_ptr<const T> unpackb(std::shared_ptr<const Bytes> bytes) {
  bool ok = T::verify_data(bytes);
  if (!ok)
    throw std::runtime_error("Bad buffer");
  return std::make_shared<T>(bytes);
}
template <typename T>
std::shared_ptr<const T> unpackb(const py::bytes &py_bytes) {
  auto bytes_ptr = std::make_shared<const Bytes>(py_bytes);
  return unpackb<T>(bytes_ptr);
}
template <typename T> std::shared_ptr<const T> unpackb(py::buffer &buffer) {
  auto bytes_ptr = std::make_shared<const Bytes>(buffer);
  return unpackb<T>(bytes_ptr);
}

} // namespace flatboobs

#endif // FLATBOOBS_CONTAINER_HPP
