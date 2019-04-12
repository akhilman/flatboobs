#ifndef FLATBOOBS_VECTOR_HPP_
#define FLATBOOBS_VECTOR_HPP_

#include <flatboobs/builder.hpp>
#include <flatboobs/message.hpp>
#include <flatboobs/types.hpp>
#include <flatbuffers/flatbuffers.h>
#include <memory>
#include <string_view>
#include <vector>

namespace flatboobs {

template <typename VT> class VectorIterator {
public:
  using vector_type = VT;
  using difference_type = std::ptrdiff_t;
  using value_type = typename VT::value_type;
  using pointer = value_type *;
  using reference = value_type &;
  using iterator_category = std::random_access_iterator_tag;
  // TODO use contiguous_iterator_tag in C++20

  VectorIterator(const vector_type *_vec, difference_type _index) noexcept
      : vec_{_vec}, index_{_index} {}

  VectorIterator &operator+=(difference_type _diff) {
    index_ += _diff;
    return *this;
  }
  VectorIterator &operator-=(difference_type _diff) {
    index_ -= _diff;
    return *this;
  }

  VectorIterator &operator+(difference_type _diff) {
    VectorIterator tmp = *this;
    return tmp += _diff;
  }
  VectorIterator &operator-(difference_type _diff) {
    VectorIterator tmp = *this;
    return tmp -= _diff;
  }

  VectorIterator &operator++() {
    index_++;
    return *this;
  }
  VectorIterator operator++(int) {
    auto tmp = index_;
    index_++;
    return VectorIterator(vec_, tmp);
  }
  VectorIterator &operator--() {
    index_--;
    return *this;
  }
  VectorIterator operator--(int) {
    auto tmp = index_;
    index_--;
    return VectorIterator(vec_, tmp);
  }

  bool operator<(VectorIterator other) { return this->index_ < other.index_; }
  bool operator>(VectorIterator other) { return this->index_ > other.index_; }
  bool operator<=(VectorIterator other) { return this->index_ <= other.index_; }
  bool operator>=(VectorIterator other) { return this->index_ >= other.index_; }

  value_type operator[](difference_type idx) { return vec_->at(idx); }

  value_type operator*() const { return vec_->at(index_); }
  friend bool operator==(const VectorIterator &lhs, const VectorIterator &rhs) {
    return lhs.index_ == rhs.index_;
  }
  friend bool operator!=(const VectorIterator &lhs, const VectorIterator &rhs) {
    return lhs.index_ != rhs.index_;
  }
  friend void swap(VectorIterator &lhs, VectorIterator &rhs) {
    std::swap(lhs.vec_, rhs.vec_);
    std::swap(lhs.index_, rhs.index_);
  }

private:
  const vector_type *vec_;
  difference_type index_;
};

// Conversion helpers

struct vector_converter {
  template <typename F, typename T>
  static inline void convert(std::vector<F> &_from, std::vector<T> &_to) {
    std::transform(_from.begin(), _from.end(), std::back_inserter(_to),
                   [](F v) { return T(v); });
  }
};

struct vector_mover {
  template <typename T>
  static inline void convert(std::vector<T> &_from, std::vector<T> &_to) {
    _to.swap(_from);
  }
};

// ContiguousVector

template <typename T> class OwningContiguousVector;
template <typename T> class UnpackedContiguousVector;
template <typename T> class UnpackedVectorOfStructs;

template <typename T> class ContiguousVector : public BaseVector {
public:
  using value_type = typename std::decay_t<T>;
  using stored_type = typename std::conditional_t<
      std::is_enum_v<value_type>, std::underlying_type<value_type>,
      std::conditional<std::is_same_v<value_type, bool>, char,
                       value_type>>::type;
  using convert_helper =
      std::conditional_t<std::is_same_v<value_type, stored_type>, vector_mover,
                         vector_converter>;
  using size_type = size_t;
  using const_iterator = VectorIterator<ContiguousVector<T>>;

  class AbstractImpl {
  public:
    virtual ~AbstractImpl() = default;
    virtual stored_type at(size_type pos) const = 0;
    virtual size_type size() const noexcept = 0;
    virtual const stored_type *data() const noexcept = 0;
  };

  ContiguousVector()
      : impl_{std::make_shared<const OwningContiguousVector<T>>()} {}
  ContiguousVector(std::vector<value_type> _vec) {
    std::vector<stored_type> tmp{};
    // Tell me if you know how to make conversion better
    convert_helper::convert(_vec, tmp);
    impl_ = std::make_shared<const OwningContiguousVector<T>>(std::move(tmp));
  }
  explicit ContiguousVector(Message _message,
                            const flatbuffers::Vector<stored_type> *_fbvec)
      : impl_{std::make_shared<const UnpackedContiguousVector<T>>(
            std::move(_message), _fbvec)} {}
  // Vector of structs
  explicit ContiguousVector(
      Message _message, const flatbuffers::Vector<const stored_type *> *_fbvec)
      : impl_{std::make_shared<const UnpackedVectorOfStructs<T>>(
            std::move(_message), _fbvec)} {}
  /*
  // Vector of tables
  explicit ContiguousVector(
      Message _message,
      const flatbuffers::Vector<
          flatbuffers::Offset<typename stored_type::flatbuffer_type>> *_fbvec)
      : impl_{std::make_shared<const UnpackedContiguousVector<T>>(
            std::move(_message), _fbvec)} {}
  */

  value_type at(size_type pos) const { return value_type(impl_->at(pos)); }
  value_type operator[](size_type pos) const { return at(pos); }

  value_type front() const { return at(0); }
  value_type back() const { return at(size() - 1); }

  VectorIterator<ContiguousVector> begin() const {
    return VectorIterator(this, 0);
  }
  VectorIterator<ContiguousVector> end() const {
    return VectorIterator(this, size());
  }

  size_type size() const noexcept { return impl_->size(); }
  bool empty() const noexcept { return size() == 0; }

  const stored_type *data() const { return impl_->data(); }
  const std::string_view str() const {
    return std::string_view(reinterpret_cast<const char *>(data()),
                            size() * sizeof(stored_type));
  }

  content_id_t content_id() const { return content_id_t(data()); }

  operator bool() const { return !empty(); }

  friend bool operator==(const ContiguousVector &_lhs,
                         const ContiguousVector &_rhs) {
    if (_lhs.impl_ == _rhs.impl_)
      return true;
    if (_lhs.size() != _rhs.size())
      return false;
    auto lhs_end = _lhs.end();
    auto rhs_end = _rhs.end();
    auto pair = std::mismatch(_lhs.begin(), lhs_end, _rhs.begin(), rhs_end);
    return pair.first == lhs_end and pair.second == rhs_end;
  }
  friend bool operator==(const ContiguousVector &_lhs,
                         const std::vector<value_type> &_rhs) {
    auto lhs_end = _lhs.end();
    auto rhs_end = _rhs.end();
    auto pair = std::mismatch(_lhs.begin(), lhs_end, _rhs.begin(), rhs_end);
    return pair.first == lhs_end and pair.second == rhs_end;
  }
  template <typename Q>
  friend bool operator!=(const ContiguousVector &_lhs, const Q &_rhs) {
    return !(_lhs == _rhs);
  }

  friend std::ostream &operator<<(std::ostream &_stream,
                                  const ContiguousVector<value_type> &_vec) {
    _stream << '[';
    for (size_t i = 0; i < _vec.size(); i++) {
      if (i != 0)
        _stream << ", ";
      _stream << _vec[i];
    }
    _stream << "]";
    return _stream;
  }

private:
  std::shared_ptr<const AbstractImpl> impl_;
};

/* Concrete impl */

template <typename T>
class OwningContiguousVector : public ContiguousVector<T>::AbstractImpl {
  using proxy_type = ContiguousVector<T>;

public:
  using stored_type = typename proxy_type::stored_type;
  using size_type = typename proxy_type::size_type;

  OwningContiguousVector() : vec_{} {}
  OwningContiguousVector(const std::vector<stored_type> _vec)
      : vec_{std::move(_vec)} {}

  stored_type at(size_type _pos) const override { return vec_.at(_pos); }
  size_type size() const noexcept override { return vec_.size(); }
  const stored_type *data() const noexcept override { return vec_.data(); }

private:
  const std::vector<stored_type> vec_;
};

template <typename T>
class UnpackedContiguousVector : public ContiguousVector<T>::AbstractImpl {
  using proxy_type = ContiguousVector<T>;

public:
  using stored_type = typename proxy_type::stored_type;
  using size_type = typename proxy_type::size_type;

  UnpackedContiguousVector(Message _message,
                           const flatbuffers::Vector<stored_type> *_fbvec)
      : message_{std::move(_message)}, fbvec_{_fbvec} {}

  stored_type at(size_type _pos) const override { return fbvec_->Get(_pos); }
  size_type size() const noexcept override { return fbvec_->size(); }
  const stored_type *data() const noexcept override {
    return reinterpret_cast<const stored_type *>(fbvec_->Data());
  }

private:
  const Message message_;
  const flatbuffers::Vector<stored_type> *fbvec_;
};

template <typename T>
class UnpackedVectorOfStructs : public ContiguousVector<T>::AbstractImpl {
  using proxy_type = ContiguousVector<T>;

public:
  using stored_type = typename proxy_type::stored_type;
  using size_type = typename proxy_type::size_type;

  UnpackedVectorOfStructs(
      Message _message, const flatbuffers::Vector<const stored_type *> *_fbvec)
      : message_{std::move(_message)}, fbvec_{_fbvec} {}

  stored_type at(size_type _pos) const override { return *fbvec_->Get(_pos); }
  size_type size() const noexcept override { return fbvec_->size(); }
  const stored_type *data() const noexcept override {
    return reinterpret_cast<const stored_type *>(fbvec_->Data());
  }

private:
  const Message message_;
  const flatbuffers::Vector<const stored_type *> *fbvec_;
};

// Builder

namespace detail {

template <typename T> struct vec_of_scalars_builder {

  using value_type = T;
  using storage_type = typename ContiguousVector<T>::stored_type;
  using flatbuffers_type = flatbuffers::Vector<storage_type>;
  using offset_type = flatbuffers::Offset<flatbuffers_type>;

  static offset_type build(flatboobs::BuilderContext &_context,
                           const ContiguousVector<T> &_vec) {

    flatbuffers::FlatBufferBuilder *fbb = _context.builder();
    offset_type offset = fbb->CreateVector(_vec.data(), _vec.size());

    return offset;
  }
};

template <typename T> struct vec_of_structs_builder {

  using value_type = T;
  using storage_type = T;
  using flatbuffers_type = flatbuffers::Vector<const storage_type *>;
  using offset_type = flatbuffers::Offset<flatbuffers_type>;

  static offset_type build(flatboobs::BuilderContext &_context,
                           const ContiguousVector<T> &_vec) {

    flatbuffers::FlatBufferBuilder *fbb = _context.builder();
    offset_type offset = fbb->CreateVectorOfStructs(_vec.data(), _vec.size());

    return offset;
  }
};
} // namespace detail

template <typename T,
          typename helper = typename std::conditional<
              std::is_scalar_v<T>, detail::vec_of_scalars_builder<T>,
              detail::vec_of_structs_builder<T>>::type>
typename helper::offset_type build(flatboobs::BuilderContext &_context,
                                   const ContiguousVector<T> &_vec,
                                   bool _is_root = true) {

  using offset_type = typename helper::offset_type;

  auto it = _context.offset_map().find(_vec.content_id());
  if (it != _context.offset_map().end())
    return offset_type{it->second};

  offset_type offset = helper::build(_context, _vec);
  _context.offset_map()[_vec.content_id()] = offset.o;

  return offset;
}

} // namespace flatboobs

#endif // FLATBOOBS_VECTOR_HPP_
