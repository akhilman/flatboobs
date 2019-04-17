
#ifndef FLATBOOBS_BUILDER_HPP
#define FLATBOOBS_BUILDER_HPP

#include <flatboobs/types.hpp>
#include <flatbuffers/flatbuffers.h>

namespace flatboobs {

struct BuilderContext {

  flatbuffers::FlatBufferBuilder *fbb_;
  offset_map_t offset_map_;

  BuilderContext(flatbuffers::FlatBufferBuilder *_fbb)
      : fbb_{_fbb}, offset_map_{} {
    fbb_->Reset();
  }

  flatbuffers::FlatBufferBuilder *builder() { return fbb_; }
  offset_map_t &offset_map() { return offset_map_; }
};

} // namespace flatboobs

#endif // FLATBOOBS_BUILDER_HPP
