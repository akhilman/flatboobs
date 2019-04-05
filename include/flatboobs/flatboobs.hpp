#ifndef FLATBOOBS_FLATBOOBS_HPP
#define FLATBOOBS_FLATBOOBS_HPP

#include <flatbuffers/flatbuffers.h>

#include <flatboobs/builder.hpp>
#include <flatboobs/data.hpp>

namespace flatboobs {

template <typename T> flatboobs::Data pack(T _table) {

  flatbuffers::FlatBufferBuilder fbb{1024};
  BuilderContext context{&fbb};

  build(context, _table);

  BuiltData built_data{};
  built_data.steal_from_builder(std::move(fbb));
  Data data{std::move(built_data)};

  return data;
}

template <typename T> const T unpack(Data _data) { return T(_data); }

} // namespace flatboobs

#endif // FLATBOOBS_FLATBOOBS_HPP
