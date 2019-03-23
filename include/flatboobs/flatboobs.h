#ifndef FLATBOOBS_FLATBOOBS_H
#define FLATBOOBS_FLATBOOBS_H

#include <flatbuffers/flatbuffers.h>

namespace flatboobs {

template <typename T> class IData {
public:
  using value_type = T;

  virtual ~IData() = default;
  virtual const value_type *data() const = 0;
  virtual const size_t size() const = 0;

  virtual operator const value_type *() const { return data(); }
  virtual const std::string_view str() const {
    return std::string_view(reinterpret_cast<const char *>(data()),
                            size() * sizeof(value_type));
  }
};

class IByteData : public IData<std::byte> {};

class BuiltByteData : public IByteData {
public:
  BuiltByteData() : size_{0}, offset_{0}, data_{nullptr} {}

  void steal_from_builder(flatbuffers::FlatBufferBuilder &&builder) {
    size_ = builder.GetSize();
    size_t buffer_size; // total buffer size with usless padding.
    const std::byte *data = reinterpret_cast<const std::byte *>(
        builder.ReleaseRaw(buffer_size, offset_));
    data_ = std::unique_ptr<const std::byte>(data);
  };

  virtual const std::byte *data() const { return data_.get() + offset_; }
  virtual const size_t size() const { return size_; }

private:
  size_t size_;
  size_t offset_;
  std::unique_ptr<const std::byte> data_;
}; // namespace flatboobs

} // namespace flatboobs

#endif // FLATBOOBS_FLATBOOBS_H
