#ifndef FLATBOOBS_FLATBOOBS_HPP
#define FLATBOOBS_FLATBOOBS_HPP

#include <flatbuffers/flatbuffers.h>

#include <flatboobs/builder.hpp>
#include <flatboobs/message.hpp>

namespace flatboobs {

template <typename T> flatboobs::Message pack(T _table) {

  flatbuffers::FlatBufferBuilder fbb{1024};
  BuilderContext context{&fbb};

  build(context, _table);

  BuiltMessage built_message{};
  built_message.steal_from_builder(std::move(fbb));
  Message message{std::move(built_message)};

  return message;
}

template <typename T> const T unpack(Message _message) { return T(_message); }

} // namespace flatboobs

#endif // FLATBOOBS_FLATBOOBS_HPP
