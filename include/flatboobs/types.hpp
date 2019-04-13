#ifndef FLATBOOBS_TYPES_HPP_
#define FLATBOOBS_TYPES_HPP_

#include <flatbuffers/flatbuffers.h>
#include <map>
#include <type_traits>

namespace flatboobs {

using content_id_t = size_t;
using offset_map_t = std::map<flatboobs::content_id_t, flatbuffers::uoffset_t>;

struct BaseStruct {};
struct BaseTable {};
struct BaseVector {};

template <typename T> struct is_struct {
  static constexpr bool value = std::is_base_of_v<BaseStruct, T>;
};
template <typename T> inline constexpr bool is_struct_v = is_struct<T>::value;

template <typename T> struct is_table {
  static constexpr bool value = std::is_base_of_v<BaseTable, T>;
};
template <typename T> inline constexpr bool is_table_v = is_table<T>::value;

template <typename T> struct is_vector {
  static constexpr bool value = std::is_base_of_v<BaseVector, T>;
};
template <typename T> inline constexpr bool is_vector_v = is_vector<T>::value;

} // namespace flatboobs

#endif // FLATBOOBS_TYPES_HPP_
