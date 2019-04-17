#ifndef FLATBOOBS_VECTOR_HPP_
#define FLATBOOBS_VECTOR_HPP_

#include <flatboobs/builder.hpp>
#include <flatboobs/message.hpp>
#include <flatboobs/types.hpp>
#include <flatbuffers/flatbuffers.h>
#include <memory>
#include <string_view>
#include <type_traits>
#include <vector>

namespace flatboobs {

template <typename T> class Vector;

namespace detail {
namespace vector {

template <typename T> struct options;

/*
 * Impl
 */

template <typename V> class AbstractImpl {
public:
  using data_ptr_type = typename V::data_ptr_type;
  using return_value_type = typename V::return_value_type;
  using size_type = typename V::size_type;
  using value_type = typename V::value_type;

  virtual ~AbstractImpl() = default;
  virtual return_value_type at(size_t pos) const = 0;
  virtual size_t size() const noexcept = 0;
  virtual data_ptr_type data() const noexcept = 0;
  virtual content_id_t content_id() const noexcept = 0;
};

template <typename V> class OwningImpl : public AbstractImpl<V> {
public:
  using data_ptr_type = typename V::data_ptr_type;
  using return_value_type = typename V::return_value_type;
  using size_type = typename V::size_type;
  using value_type = typename V::value_type;
  static_assert(!std::is_reference_v<return_value_type>);

  OwningImpl() noexcept : vec_{} {}
  OwningImpl(std::vector<value_type> _vec) noexcept : vec_{std::move(_vec)} {}

  return_value_type at(size_type _pos) const override {
    return return_value_type(vec_.at(_pos));
  }
  size_type size() const noexcept override { return vec_.size(); }
  data_ptr_type data() const noexcept override { return nullptr; }
  content_id_t content_id() const noexcept override {
    return content_id_t(&vec_);
  }

private:
  const std::vector<value_type> vec_;
};

template <typename V> class OwningDirectImpl : public AbstractImpl<V> {
public:
  using data_ptr_type = typename V::data_ptr_type;
  using return_value_type = typename V::return_value_type;
  using size_type = typename V::size_type;
  using value_type = typename V::value_type;
  static_assert(sizeof(std::remove_pointer_t<data_ptr_type>) ==
                sizeof(value_type));

  OwningDirectImpl() noexcept : vec_{} {}
  OwningDirectImpl(std::vector<value_type> _vec) noexcept
      : vec_{std::move(_vec)} {}

  return_value_type at(size_type _pos) const override { return vec_.at(_pos); }
  size_type size() const noexcept override { return vec_.size(); }
  data_ptr_type data() const noexcept override {
    return reinterpret_cast<data_ptr_type>(vec_.data());
  }
  content_id_t content_id() const noexcept override {
    return content_id_t(&vec_);
  }

private:
  const std::vector<value_type> vec_;
};

template <typename V> class UnpackedBoolsImpl : public AbstractImpl<V> {
public:
  using fb_value_type = typename V::fb_value_type;
  using data_ptr_type = typename V::data_ptr_type;
  using return_value_type = typename V::return_value_type;
  using size_type = typename V::size_type;

  UnpackedBoolsImpl(Message _message,
                    const flatbuffers::Vector<fb_value_type> *_fbvec) noexcept
      : message_{std::move(_message)}, fbvec_{_fbvec} {}

  return_value_type at(size_type _pos) const override {
    return this->fbvec_->Get(_pos);
  }
  data_ptr_type data() const noexcept override { return nullptr; }

  size_type size() const noexcept override { return fbvec_->size(); }
  content_id_t content_id() const noexcept override {
    return content_id_t(fbvec_);
  }

private:
  const Message message_;
  const flatbuffers::Vector<fb_value_type> *fbvec_;
};

template <typename V> class UnpackedScalarsImpl : public AbstractImpl<V> {
public:
  using data_ptr_type = typename V::data_ptr_type;
  using fb_value_type = typename V::fb_value_type;
  using return_value_type = typename V::return_value_type;
  using size_type = typename V::size_type;
  static_assert(!std::is_reference_v<return_value_type>);
  static_assert(sizeof(std::remove_pointer_t<data_ptr_type>) ==
                sizeof(fb_value_type));

  UnpackedScalarsImpl(Message _message,
                      const flatbuffers::Vector<fb_value_type> *_fbvec) noexcept
      : message_{std::move(_message)}, fbvec_{_fbvec} {}

  return_value_type at(size_type _pos) const override {
    return return_value_type(this->fbvec_->Get(_pos));
  }
  data_ptr_type data() const noexcept override {
    return reinterpret_cast<data_ptr_type>(this->fbvec_->Data());
  }

  size_type size() const noexcept override { return fbvec_->size(); }
  content_id_t content_id() const noexcept override {
    return content_id_t(fbvec_);
  }

private:
  const Message message_;
  const flatbuffers::Vector<fb_value_type> *fbvec_;
};

template <typename V> class UnpackedStructsImpl : public AbstractImpl<V> {
public:
  using data_ptr_type = typename V::data_ptr_type;
  using fb_value_type = typename V::fb_value_type;
  using return_value_type = typename V::return_value_type;
  using size_type = typename V::size_type;
  using value_type = typename V::value_type;
  static_assert(std::is_same_v<data_ptr_type, fb_value_type>);
  static_assert(std::is_same_v<const value_type *, fb_value_type>);
  static_assert(
      std::is_same_v<const std::decay_t<return_value_type> *, fb_value_type>);

  UnpackedStructsImpl(Message _message,
                      const flatbuffers::Vector<fb_value_type> *_fbvec) noexcept
      : message_{std::move(_message)}, fbvec_{_fbvec} {}

  return_value_type at(size_type _pos) const override {
    return *(this->fbvec_->Get(_pos));
  }
  data_ptr_type data() const noexcept override {
    return reinterpret_cast<const value_type *>(this->fbvec_->Data());
  }

  size_type size() const noexcept override { return fbvec_->size(); }
  content_id_t content_id() const noexcept override {
    return content_id_t(fbvec_);
  }

private:
  const Message message_;
  const flatbuffers::Vector<fb_value_type> *fbvec_;
};

/*
 * Accesssor
 */

template <typename V> struct DirectAccessor {
  using abstract_impl_type = AbstractImpl<V>;
  using data_ptr_type = typename V::data_ptr_type;
  using return_value_type = typename V::return_value_type;
  using size_type = typename V::size_type;
  using value_type = typename V::value_type;
  static_assert(sizeof(std::remove_pointer_t<data_ptr_type>) ==
                sizeof(value_type));
  static_assert(std::is_same_v<std::decay_t<return_value_type>, value_type>);

  DirectAccessor(const abstract_impl_type *_impl) noexcept
      : impl_{_impl}, data_{_impl->data()} {}
  inline return_value_type at(size_type _pos) const noexcept {
    return *reinterpret_cast<const value_type *>(data_ + _pos);
  }

private:
  const abstract_impl_type *impl_;
  data_ptr_type data_;
};

template <typename V> struct ImplAccessor {
  using abstract_impl_type = AbstractImpl<V>;
  using return_value_type = typename V::return_value_type;
  using size_type = typename V::size_type;

  ImplAccessor(const abstract_impl_type *_impl) noexcept : impl_{_impl} {}
  inline return_value_type at(size_type _pos) const { return impl_->at(_pos); }

private:
  const abstract_impl_type *impl_;
};

/*
 * Builder
 */

template <typename T, typename V> struct ScalarBuilder {
  using offset_type = typename V::offset_type;
  using data_ptr_type = typename V::data_ptr_type;
  using fb_value_type = typename V::fb_value_type;

  static_assert(
      std::is_same_v<std::decay_t<std::remove_pointer_t<data_ptr_type>>,
                     fb_value_type>);

  static inline const offset_type build(flatboobs::BuilderContext &_context,
                                        const Vector<T> &_vec) {

    flatbuffers::FlatBufferBuilder *fbb = _context.builder();
    const offset_type offset = fbb->CreateVector(_vec.data(), _vec.size());

    return offset;
  }
};

template <typename T, typename V> struct BoolBuilder {
  using data_ptr_type = typename V::data_ptr_type;
  using fb_value_type = typename V::fb_value_type;
  using offset_type = typename V::offset_type;
  using return_value_type = typename V::return_value_type;
  static_assert(std::is_same_v<return_value_type, bool>);
  static_assert(std::is_same_v<fb_value_type, uint8_t>);

  static inline const offset_type build(flatboobs::BuilderContext &_context,
                                        const Vector<T> &_vec) {

    using std::crbegin;
    using std::crend;
    using std::size;

    flatbuffers::FlatBufferBuilder *fbb = _context.builder();
    fbb->StartVector(size(_vec), sizeof(fb_value_type));

    for (auto iter = crbegin(_vec); iter < crend(_vec); iter++)
      fbb->PushElement(*iter);

    const offset_type offset = fbb->EndVector(size(_vec));

    return offset;
  }
};

template <typename T, typename V> struct StructBuilder {
  using offset_type = typename V::offset_type;
  using data_ptr_type = typename V::data_ptr_type;
  using fb_value_type = typename V::fb_value_type;

  static_assert(std::is_same_v<data_ptr_type, fb_value_type>);

  static inline const offset_type build(flatboobs::BuilderContext &_context,
                                        const Vector<T> &_vec) {

    flatbuffers::FlatBufferBuilder *fbb = _context.builder();
    const offset_type offset =
        fbb->CreateVectorOfStructs(_vec.data(), _vec.size());

    return offset;
  }
};

/*
 * Vector properties
 */

template <typename T> struct scalar_options {
  using V = scalar_options<T>;
  using size_type = size_t;
  using difference_type = std::ptrdiff_t;
  using value_type = typename std::decay_t<T>;
  using return_value_type = value_type;
  using data_ptr_type = const value_type *;
  using fb_value_type = value_type;
  using offset_type = flatbuffers::Offset<flatbuffers::Vector<fb_value_type>>;
  using accessor_type = DirectAccessor<V>;
  using owning_impl_type = OwningDirectImpl<V>;
  using unpacked_impl_type = UnpackedScalarsImpl<V>;
  using builder_type = ScalarBuilder<T, V>;
};

template <typename T> struct struct_options {
  using V = struct_options<T>;
  using size_type = size_t;
  using difference_type = std::ptrdiff_t;
  using value_type = typename std::decay_t<T>;
  using return_value_type = const value_type &;
  using data_ptr_type = const value_type *;
  using fb_value_type = const value_type *;
  using offset_type = flatbuffers::Offset<flatbuffers::Vector<fb_value_type>>;
  using accessor_type = DirectAccessor<V>;
  using owning_impl_type = OwningDirectImpl<V>;
  using unpacked_impl_type = UnpackedStructsImpl<V>;
  using builder_type = StructBuilder<T, V>;
};

template <typename T> struct enum_options {
  using V = enum_options<T>;
  using size_type = size_t;
  using difference_type = std::ptrdiff_t;
  using value_type = typename std::decay_t<T>;
  using return_value_type = value_type;
  using data_ptr_type = const std::underlying_type_t<value_type> *;
  using fb_value_type = std::underlying_type_t<value_type>;
  using offset_type = flatbuffers::Offset<flatbuffers::Vector<fb_value_type>>;
  using accessor_type = DirectAccessor<V>;
  using owning_impl_type = OwningDirectImpl<V>;
  using unpacked_impl_type = UnpackedScalarsImpl<V>;
  using builder_type = ScalarBuilder<T, V>;
};

template <typename T> struct bool_options {
  using V = bool_options<T>;
  using size_type = size_t;
  using difference_type = std::ptrdiff_t;
  using value_type = bool;
  using return_value_type = value_type;
  using data_ptr_type = void *;
  using fb_value_type = uint8_t;
  using offset_type = flatbuffers::Offset<flatbuffers::Vector<fb_value_type>>;
  using accessor_type = ImplAccessor<V>;
  using owning_impl_type = OwningImpl<V>;
  using unpacked_impl_type = UnpackedBoolsImpl<V>;
  using builder_type = BoolBuilder<T, V>;
};

/*
template <typename T> struct table_options {
  using V = table_options<T>;
  using size_type = size_t;
  using difference_type = std::ptrdiff_t;
  using value_type = typename std::decay_t<T>;
  using return_value_type = value_type;
  using data_ptr_type = void *;
  using fb_value_type =
      flatbuffers::Offset<typename value_type::flatbuffer_type>;
  using offset_type = flatbuffers::Offset<flatbuffers::Vector<fb_value_type>>;
  using accessor_type = ImplAccessor<V>;
  using owning_impl_type = OwningImpl<V>;
  using unpacked_impl_type = UnpackedTablesImpl<V>;
  using builder_type = TableBuilder<T, V>;
};

template <typename T> struct union_options {
  using V = union_options<T>;
  using size_type = size_t;
  using difference_type = std::ptrdiff_t;
  using value_type = typename std::decay_t<T>;
  using return_value_type = value_type;
  using data_ptr_type = void *;
  using fb_value_type = flatbuffers::Offset<void>;
  using offset_type = flatbuffers::Offset<flatbuffers::Vector<fb_value_type>>;
  using accessor_type = ImplAccessor<V>;
  using owning_impl_type = OwningImpl<V>;
  using unpacked_impl_type = UnpackeUnionsImpl<V>;
  using builder_type = UnionBuilder<T, V>;
};
*/

template <typename T> struct options {
  using value_type = std::decay_t<T>;
  using type = std::conditional_t<
      std::is_same_v<value_type, bool>, bool_options<value_type>,
      std::conditional_t<
          std::is_enum_v<value_type>, enum_options<value_type>,
          std::conditional_t<
              std::is_scalar_v<value_type>, scalar_options<value_type>,
              std::conditional_t<is_struct_v<value_type>,
                                 struct_options<value_type>, void>>>>;
  static_assert(!std::is_void_v<type>);
};

template <typename T> using options_t = typename options<T>::type;

} // namespace vector
} // namespace detail

/*
 * Iterator
 */

template <typename T> class VectorIterator {
  using V = detail::vector::options_t<T>;

public:
  using abstract_impl_type = detail::vector::AbstractImpl<V>;
  using accessor_type = typename V::accessor_type;
  using return_value_type = typename V::return_value_type;
  using size_type = typename V::size_type;

  using iterator_category = std::random_access_iterator_tag;
  using value_type = typename V::value_type;
  using reference = return_value_type;
  using difference_type = typename V::difference_type;
  using pointer = const value_type *;

  VectorIterator(accessor_type _accessor, size_type _pos)
      : accessor_{std::move(_accessor)}, index_{_pos} {}

  return_value_type operator[](difference_type _pos) {
    return accessor_.at(index_ + _pos);
  }
  return_value_type operator*() const { return accessor_.at(index_); }

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
    return VectorIterator(accessor_, tmp);
  }

  VectorIterator &operator--() {
    index_--;
    return *this;
  }
  VectorIterator operator--(int) {
    auto tmp = index_;
    index_--;
    return VectorIterator(accessor_, tmp);
  }

  friend bool operator<(const VectorIterator &lhs, const VectorIterator &rhs) {
    return lhs.index_ < rhs.index_;
  }
  friend bool operator>(const VectorIterator &lhs, const VectorIterator &rhs) {
    return lhs.index_ > rhs.index_;
  }
  friend bool operator<=(const VectorIterator &lhs, const VectorIterator &rhs) {
    return lhs.index_ <= rhs.index_;
  }
  friend bool operator>=(const VectorIterator &lhs, const VectorIterator &rhs) {
    return lhs.index_ >= rhs.index_;
  }
  friend bool operator==(const VectorIterator &lhs, const VectorIterator &rhs) {
    return lhs.index_ == rhs.index_;
  }
  friend bool operator!=(const VectorIterator &lhs, const VectorIterator &rhs) {
    return lhs.index_ != rhs.index_;
  }

  friend void swap(VectorIterator &lhs, VectorIterator &rhs) noexcept {
    std::swap(lhs.accessor_, rhs.accessor_);
    std::swap(lhs.index_, rhs.index_);
  }

private:
  accessor_type accessor_;
  size_type index_;
};

/*
 * Vector
 */

template <typename T, typename D> class VectorDataAccessMixin;
template <typename T> class VectorDataAccessMixin<T, void *> {
  friend Vector<T>;
  VectorDataAccessMixin(){};
};
template <typename T, typename D> class VectorDataAccessMixin {
public:
  using data_ptr_type = D;
  data_ptr_type data() const noexcept {
    static_assert(!std::is_void_v<std::remove_pointer_t<data_ptr_type>>,
                  "Raw data access disabled for this type.");
    return underlying()->impl_->data();
  }
  std::string_view str() const {
    return std::string_view(
        reinterpret_cast<const char *>(underlying()->data()),
        underlying()->size() * sizeof(std::remove_pointer_t<data_ptr_type>));
  }

private:
  friend Vector<T>;
  VectorDataAccessMixin() noexcept {};

  inline const Vector<T> *underlying() const noexcept {
    return static_cast<const Vector<T> *>(this);
  }
};

template <typename T>
class Vector : public BaseVector,
               public VectorDataAccessMixin<
                   T, typename detail::vector::options_t<T>::data_ptr_type> {
  using V = detail::vector::options_t<T>;

public:
  using abstract_impl_type = detail::vector::AbstractImpl<V>;
  using accessor_type = typename V::accessor_type;
  using iterator = VectorIterator<T>;
  using data_ptr_type = typename V::data_ptr_type;
  using owning_impl_type = typename V::owning_impl_type;
  using return_value_type = typename V::return_value_type;
  using size_type = typename V::size_type;
  using unpacked_impl_type = typename V::unpacked_impl_type;
  using value_type = typename V::value_type;

  Vector()
      : impl_{std::make_shared<const owning_impl_type>()}, accessor_{
                                                               impl_.get()} {}
  Vector(std::vector<T> _vec)
      : impl_{std::make_shared<const owning_impl_type>(std::move(_vec))},
        accessor_{impl_.get()} {}
  template <typename... Ts>
  explicit Vector(Message _message, Ts... _args)
      : impl_{std::make_shared<const unpacked_impl_type>(
            std::move(_message), std::forward<Ts>(_args)...)},
        accessor_{impl_.get()} {}

  return_value_type at(size_type _pos) const { return accessor_.at(_pos); }
  return_value_type operator[](size_type _pos) const {
    return accessor_.at(_pos);
  }

  return_value_type front() const { return at(0); }
  return_value_type back() const { return at(size() - 1); }

  iterator begin() const { return iterator(accessor_, 0); }
  iterator end() const { return iterator(accessor_, size()); }
  std::reverse_iterator<iterator> rbegin() const {
    return std::make_reverse_iterator(end());
  }
  std::reverse_iterator<iterator> rend() const {
    return std::make_reverse_iterator(begin());
  }

  size_type size() const noexcept { return impl_->size(); }
  bool empty() const noexcept { return size() == 0; }

  content_id_t content_id() const noexcept {
    return content_id_t(impl_->content_id());
  }

  operator bool() const noexcept { return !empty(); }

  friend bool operator==(const Vector &_lhs, const Vector &_rhs) {
    if (_lhs.impl_ == _rhs.impl_)
      return true;
    if (_lhs.size() != _rhs.size())
      return false;
    auto lhs_end = _lhs.end();
    auto rhs_end = _rhs.end();
    auto pair = std::mismatch(_lhs.begin(), lhs_end, _rhs.begin(), rhs_end);
    return pair.first == lhs_end and pair.second == rhs_end;
  }
  friend bool operator==(const Vector &_lhs,
                         const std::vector<value_type> &_rhs) {
    auto lhs_end = _lhs.end();
    auto rhs_end = _rhs.end();
    auto pair = std::mismatch(_lhs.begin(), lhs_end, _rhs.begin(), rhs_end);
    return pair.first == lhs_end and pair.second == rhs_end;
  }
  friend bool operator!=(const Vector &_lhs, const Vector &_rhs) {
    return !(_lhs == _rhs);
  }
  friend bool operator!=(const Vector &_lhs,
                         const std::vector<value_type> &_rhs) {
    return !(_lhs == _rhs);
  }

  friend std::ostream &operator<<(std::ostream &_stream,
                                  const Vector<value_type> &_vec) {
    _stream << '[';
    for (size_type i = 0; i < _vec.size(); i++) {
      if (i != 0)
        _stream << ", ";
      if constexpr (std::is_same_v<value_type, bool>)
        _stream << (_vec[i] ? "true" : "false");
      else if constexpr (!std::is_enum_v<value_type> &&
                         std::is_scalar_v<value_type>)
        _stream << +_vec[i];
      else
        _stream << _vec[i];
    }
    _stream << ']';
    return _stream;
  }

private:
  friend VectorDataAccessMixin<T, data_ptr_type>;
  std::shared_ptr<const abstract_impl_type> impl_;
  accessor_type accessor_;
};

// Builder

template <typename T>
const typename detail::vector::options_t<T>::offset_type
build(flatboobs::BuilderContext &_context, const Vector<T> &_vec,
      bool _is_root = false) {

  using V = detail::vector::options_t<T>;
  using offset_type = typename V::offset_type;
  using builder_type = typename V::builder_type;

  auto it = _context.offset_map().find(_vec.content_id());
  if (it != _context.offset_map().end())
    return offset_type{it->second};

  const offset_type offset = builder_type::build(_context, _vec);
  _context.offset_map()[_vec.content_id()] = offset.o;

  return offset;
}

} // namespace flatboobs

#endif // FLATBOOBS_VECTOR_HPP_
