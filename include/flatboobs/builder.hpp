
#ifndef FLATBOOBS_BUILDER_HPP
#define FLATBOOBS_BUILDER_HPP

#include <flatbuffers/flatbuffers.h>
#include <map>

namespace flatboobs {

using content_id_t = size_t;
using offset_map_t = std::map<flatboobs::content_id_t, flatbuffers::uoffset_t>;

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
