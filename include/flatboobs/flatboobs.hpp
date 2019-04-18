#ifndef FLATBOOBS_FLATBOOBS_HPP
#define FLATBOOBS_FLATBOOBS_HPP

#include <flatbuffers/flatbuffers.h>

#include <flatboobs/builder.hpp>
#include <flatboobs/exceptions.hpp>
#include <flatboobs/message.hpp>
#include <flatboobs/types.hpp>
#include <flatboobs/vector.hpp>

namespace flatboobs {

template <typename T> Message pack(T _table) {

  const Message *source_message = _table.source_message();
  if (source_message) {
    content_id_t source_content_id =
        content_id_t(flatbuffers::GetRoot<void>(source_message->data()));
    if (source_content_id == _table.content_id())
      return Message{*source_message};
  }

  flatbuffers::FlatBufferBuilder fbb{1024};
  BuilderContext context{&fbb};

  _table.build(context, true);

  BuiltMessage built_message{};
  built_message.steal_from_builder(fbb);
  Message message{std::move(built_message)};

  return message;
}

template <typename T> T unpack(Message _message) { return T(_message); }

} // namespace flatboobs

#endif // FLATBOOBS_FLATBOOBS_HPP
