#ifndef FLATBOOBS_DATA_HPP_
#define FLATBOOBS_DATA_HPP_

#include <flatbuffers/flatbuffers.h>
#include <memory>
#include <ostream>

namespace flatboobs {

class Message;

struct MessageIterator {
  using difference_type = std::ptrdiff_t;
  using value_type = const std::byte;
  using pointer = const std::byte *;
  using reference = const std::byte &;
  using iterator_category = std::random_access_iterator_tag;
  // TODO use contiguous_iterator_tag in C++20

  MessageIterator(pointer _ptr = 0) noexcept : ptr_{_ptr} {}

  MessageIterator &operator+=(difference_type _diff) {
    ptr_ += _diff;
    return *this;
  }
  MessageIterator &operator-=(difference_type _diff) {
    ptr_ -= _diff;
    return *this;
  }

  MessageIterator &operator+(difference_type _diff) {
    MessageIterator tmp = *this;
    return tmp += _diff;
  }
  MessageIterator &operator-(difference_type _diff) {
    MessageIterator tmp = *this;
    return tmp -= _diff;
  }

  MessageIterator &operator++() {
    ptr_++;
    return *this;
  }
  MessageIterator operator++(int) {
    auto tmp = ptr_;
    ptr_++;
    return MessageIterator(tmp);
  }
  MessageIterator &operator--() {
    ptr_--;
    return *this;
  }
  MessageIterator operator--(int) {
    auto tmp = ptr_;
    ptr_--;
    return MessageIterator(tmp);
  }

  bool operator<(MessageIterator other) { return this->ptr_ < other.ptr_; }
  bool operator>(MessageIterator other) { return this->ptr_ > other.ptr_; }
  bool operator<=(MessageIterator other) { return this->ptr_ <= other.ptr_; }
  bool operator>=(MessageIterator other) { return this->ptr_ >= other.ptr_; }

  reference operator[](difference_type idx) { return *(ptr_ + idx); }

  reference operator*() const { return *ptr_; }
  friend bool operator==(const MessageIterator &lhs,
                         const MessageIterator &rhs) {
    return lhs.ptr_ == rhs.ptr_;
  }
  friend bool operator!=(const MessageIterator &lhs,
                         const MessageIterator &rhs) {
    return lhs.ptr_ != rhs.ptr_;
  }
  pointer operator->() const { return ptr_; }
  friend void swap(MessageIterator &lhs, MessageIterator &rhs) {
    std::swap(lhs.ptr_, rhs.ptr_);
  }

  pointer ptr_;
};

class Message {
public:
  template <typename T>
  Message(T _x) noexcept : self_{std::make_shared<model_t<T>>(std::move(_x))} {}

  const std::byte *data() const { return self_->data(); }
  size_t size() const { return self_->size(); }
  size_t lenght() const { return size(); }

  MessageIterator begin() const { return MessageIterator(data()); }
  MessageIterator end() const { return MessageIterator(data()) + size(); }

  std::reverse_iterator<MessageIterator> rbegin() const {
    return std::reverse_iterator(end());
  }
  std::reverse_iterator<MessageIterator> rend() const {
    return std::reverse_iterator(begin());
  }

  const std::string_view str() const {
    return std::string_view(reinterpret_cast<const char *>(data()), size());
  }

  friend std::ostream &operator<<(std::ostream &_stream, const Message &_data) {
    _stream << "Message(" << _data.data() << ", size=" << _data.size() << ")";
    return _stream;
  }

private:
  class concept_t {
  public:
    virtual ~concept_t() = default;
    virtual const std::byte *data() const = 0;
    virtual size_t size() const = 0;
  };

  template <typename T> class model_t final : public concept_t {
  public:
    using value_type = typename std::remove_pointer<T>::type;
    using object_type = typename std::conditional<std::is_pointer<T>::value,
                                                  int, value_type>::type;

    model_t(object_type _obj) noexcept
        : object_{std::move(_obj)}, ptr_{&object_} {};
    model_t(const value_type *_ptr) noexcept : object_{0}, ptr_{_ptr} {};

    const std::byte *data() const override {
      return reinterpret_cast<const std::byte *>(ptr_->data());
    }
    size_t size() const override {
      using item_type =
          std::remove_pointer_t<decltype(std::declval<value_type>().data())>;
      return ptr_->size() * sizeof(item_type);
    }

  private:
    const object_type object_;
    const value_type *ptr_;
  };
  std::shared_ptr<const concept_t> self_;
};

class BuiltMessage {
public:
  BuiltMessage() : size_{0}, offset_{0}, data_{nullptr} {}

  // Move
  BuiltMessage(BuiltMessage &&_other) = default;
  BuiltMessage &operator=(BuiltMessage &&_other) = default;

  // Copy
  BuiltMessage(const BuiltMessage &) = delete;
  BuiltMessage &operator=(const BuiltMessage &) = delete;

  void steal_from_builder(flatbuffers::FlatBufferBuilder &&builder) {
    size_ = builder.GetSize();
    size_t buffer_size; // total buffer size with usless padding.
    const std::byte *data = reinterpret_cast<const std::byte *>(
        builder.ReleaseRaw(buffer_size, offset_));
    data_ = std::unique_ptr<const std::byte>(data);
  };

  const std::byte *data() const { return data_.get() + offset_; }
  bool has_data() const { return data_.get() != nullptr && size_ > 0; }
  size_t size() const { return size_; }

private:
  size_t size_;
  size_t offset_;
  std::unique_ptr<const std::byte> data_;
};

} // namespace flatboobs

#endif // FLATBOOBS_DATA_HPP_
