#include <iterator>
#include <memory>
#include <sstream>
#include <string>
#include <variant>
#include <vector>

#include <flatbuffers/hash.h>
#include <flatbuffers/idl.h>
#include <flatbuffers/util.h>
// #include <flatbuffers/flatbuffers.h>  # used by dump/load bfbs
// #include <flatbuffers/reflection.h>  # used by dump/load bfbs

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace flatboobs {

using namespace pybind11::literals;
namespace fb = flatbuffers;
namespace py = pybind11;

#define RETPOL_REFINT py::return_value_policy::reference_internal
#define RETPOL_TAKEOWN py::return_value_policy::take_ownership
#define RETPOL_COPY py::return_value_policy::copy

fb::IDLOptions parser_options() {
  auto options = fb::IDLOptions{};
  options.lang = fb::IDLOptions::kCpp;
  return options;
}

// TODO move to header
class ParserError : public std::exception {
  const std::string message;

public:
  ParserError(const std::string message_) : message{message_} {};
  ParserError(const char *message_) : message{message_} {};
  virtual const char *what() const throw() { return message.c_str(); }
};

// TODO move to header
class NotImplementedError : public std::exception {
public:
  virtual const char *what() const throw() { return "Not implemented"; }
};

fb::Parser *parse_file(const std::string &source_filename,
                       const std::vector<std::string> &include_paths,
                       const bool hash_identifier = false) {
  bool ok;
  std::stringstream message;

  fb::Parser *parser = new fb::Parser{parser_options()};

  std::string source;
  ok = fb::LoadFile(source_filename.c_str(), true, &source);
  if (!ok) {
    message << "No such file: \"";
    message << source_filename << "\"";
    throw ParserError{message.str()};
  }

  std::vector<const char *> c_include_paths;
  c_include_paths.reserve(include_paths.size());
  for (auto include : include_paths) {
    c_include_paths.push_back(include.c_str());
  }
  auto local_include_path = fb::StripFileName(source_filename);
  c_include_paths.push_back(local_include_path.c_str());

  if (fb::GetExtension(source_filename) == reflection::SchemaExtension()) {
    /*
    ok = parser->Deserialize(
        reinterpret_cast<const uint8_t *>(source.c_str()),
        source.size()
        );
    if (!ok) throw ParserError {
      "Unable to deserialize binary schema file " + source_filename };
    */
    throw NotImplementedError();
  } else {
    ok = parser->Parse(source.c_str(),
                       const_cast<const char **>(c_include_paths.data()),
                       source_filename.c_str());
    if (!ok)
      throw ParserError{parser->error_};
  }

  if (hash_identifier && parser->file_identifier_.empty() &&
      parser->root_struct_def_) {
    auto full_name =
        parser->root_struct_def_->defined_namespace->GetFullyQualifiedName(
            parser->root_struct_def_->name);
    uint32_t hash = fb::HashFnv1a<uint32_t>(full_name.c_str());
    char *const hash_p = reinterpret_cast<char *const>(&hash);
    for (size_t i = sizeof(hash); i > 0; i--)
      parser->file_identifier_.push_back(*(hash_p + i - 1));
  }

  return parser;
}

std::string ascii_or_hex(std::string src) {
  std::stringstream ret;
  if (src.find_first_not_of(
          "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890_") ==
      std::string::npos)
    ret << '"' << src << '"';
  else {
    ret << "0x";
    for (unsigned char c : src)
      ret << std::hex << (int)c;
  }

  return ret.str();
}

template <typename TT>
static std::vector<std::string> get_sorted_keys(const TT &table) {
  std::map<void *, std::string> keys{};
  std::vector<std::string> sorted_keys{};
  for (auto pair : table.dict)
    keys[pair.second] = pair.first;
  for (auto ptr : table.vec)
    sorted_keys.push_back(keys[ptr]);
  return sorted_keys;
}

template <typename IT>
static void add_symbol_table(py::module &m, const std::string &name) {

  using TT = fb::SymbolTable<IT>;

  py::class_<TT>(m, (name + "Table").c_str())
      .def(py::init<>())
      .def("__repr__",
           [name](const TT &self) {
             std::stringstream repr;
             repr << "<" << name << "Table: [";
             auto keys = get_sorted_keys(self);
             for (auto key : keys) {
               if (key != *keys.begin())
                 repr << ", ";
               repr << '"' << key << '"';
             }
             repr << "]>";
             return repr.str();
           })
      .def("__getitem__",
           [](const TT &self, const size_t index) {
             if (index >= self.vec.size())
               throw py::index_error("Index " + std::to_string(index) +
                                     " out of range");
             return self.vec[index];
           },
           RETPOL_REFINT)
      .def("__len__", [](const TT &self) { return self.vec.size(); })
      .def("__iter__",
           [](const TT &self) {
             return py::make_iterator(self.vec.begin(), self.vec.end());
           },
           RETPOL_REFINT)
      .def("__reversed__",
           [](const TT &self) {
             return py::make_iterator(self.vec.rbegin(), self.vec.rend());
           },
           RETPOL_REFINT)
      .def("count",
           [](const TT &self, const IT *value) {
             return std::count(self.vec.begin(), self.vec.end(), value);
           })
      .def("index",
           [](const TT &self, const IT *value) {
             auto itr = std::find(self.vec.begin(), self.vec.end(), value);
             size_t idx = -1;
             if (itr != self.vec.end())
               idx = std::distance(self.vec.begin(), itr);
             return idx;
           })
      .def("keys", [](const TT &self) { return get_sorted_keys(self); })
      .def("lookup",
           [](const TT &self, const std::string &key) {
             IT *value = self.Lookup(key);
             if (value == NULL) {
               throw py::key_error("key '" + key + "' does not exist");
             }
             return value;
           },
           RETPOL_REFINT);
}

PYBIND11_MODULE(idl, m) {
  m.doc() = "Flatbuffers idl parser.";

  // Exceptions
  py::register_exception<ParserError>(m, "ParserError");

  // Enums
  py::enum_<fb::BaseType>(m, "BaseType")
#define FLATBUFFERS_TD(ENUM, IDLTYPE, CTYPE, JTYPE, GTYPE, NTYPE, PTYPE,       \
                       RTYPE)                                                  \
  .value(#ENUM, fb::BaseType::BASE_TYPE_##ENUM)
      FLATBUFFERS_GEN_TYPES(FLATBUFFERS_TD);
#undef FLATBUFFERS_TD

  // Value
  py::class_<fb::Value>(m, "Value")
      .def(py::init<>())
      .def_readonly("type", &fb::Value::type, RETPOL_REFINT)
      .def_readonly("constant", &fb::Value::constant, RETPOL_REFINT)
      .def_readonly("offset", &fb::Value::offset, RETPOL_REFINT);
  add_symbol_table<fb::Value>(m, "Value");

  // Namespace
  py::class_<fb::Namespace>(m, "Namespace")
      .def(py::init<>())
      .def("__repr__",
           [](const fb::Namespace &self) {
             std::stringstream repr;
             repr << "<Namespace: [";
             for (auto part : self.components) {
               if (part != *self.components.begin())
                 repr << ", ";
               repr << '"' << part << '"';
             }
             repr << "]>";
             return repr.str();
           })
      .def("get_fully_qualified_name", &fb::Namespace::GetFullyQualifiedName,
           "name"_a, "max_components"_a = 1000)
      .def_readonly("components", &fb::Namespace::components, RETPOL_REFINT)
      .def_readonly("from_table", &fb::Namespace::from_table);
  add_symbol_table<fb::Namespace>(m, "Namespace");

  // Definition
  py::class_<fb::Definition>(m, "Definition")
      .def(py::init<>())
      .def("__repr__",
           [](const fb::Definition &self) {
             return "<Definition: \"" + self.name + "\">";
           })
      .def_readonly("name", &fb::Definition::name)
      .def_readonly("file", &fb::Definition::file)
      .def_readonly("doc_comment", &fb::Definition::doc_comment, RETPOL_REFINT)
      .def_readonly("attributes", &fb::Definition::attributes, RETPOL_REFINT)
      .def_readonly("generated", &fb::Definition::generated)
      .def_readonly("defined_namespace", &fb::Definition::defined_namespace,
                    RETPOL_REFINT)
      .def_property_readonly(
          "fully_qualified_name", [](const fb::Definition &self) {
            return self.defined_namespace->GetFullyQualifiedName(self.name);
          });

  // Type
  py::class_<fb::Type>(m, "Type")
      .def(py::init<>())
      .def("__eq__",
           [](const fb::Type &self, const fb::Type &other) {
             return fb::EqualByName(self, other);
           })
      .def_readonly("base_type", &fb::Type::base_type)
      .def_readonly("element", &fb::Type::element)
      .def_property_readonly(
          "definition",
          [](const fb::Type &self)
              -> std::variant<py::none, fb::StructDef *, fb::EnumDef *> {
            fb::Type type = self;
            if (type.base_type == fb::BaseType::BASE_TYPE_VECTOR)
              type = self.VectorType();
            if (type.struct_def != NULL)
              return type.struct_def;
            if (type.enum_def != NULL)
              return type.enum_def;
            return py::none();
          },
          RETPOL_REFINT)
      .def_property_readonly(
          "inline_size", [](fb::Type &self) { return fb::InlineSize(self); })
      .def_property_readonly(
          "inline_alignment",
          [](fb::Type &self) { return fb::InlineAlignment(self); })
      .def_property_readonly("is_struct",
                             [](fb::Type &self) { return fb::IsStruct(self); });
  add_symbol_table<fb::Type>(m, "Type");

  // FieldDef
  py::class_<fb::FieldDef, fb::Definition>(m, "FieldDef")
      .def(py::init<>())
      .def("__repr__",
           [](const fb::FieldDef &self) {
             return "<FieldDef: \"" + self.name + "\">";
           })
      .def_readonly("value", &fb::FieldDef::value, RETPOL_REFINT)
      .def_readonly("deprecated", &fb::FieldDef::deprecated)
      .def_readonly("required", &fb::FieldDef::required)
      .def_readonly("key", &fb::FieldDef::key)
      .def_readonly("native_inline", &fb::FieldDef::native_inline)
      .def_readonly("flexbuffer", &fb::FieldDef::flexbuffer)
      .def_readonly("nested_flatbuffer", &fb::FieldDef::nested_flatbuffer,
                    RETPOL_REFINT)
      .def_readonly("padding", &fb::FieldDef::padding);
  add_symbol_table<fb::FieldDef>(m, "FieldDef");

  // StructDef
  py::class_<fb::StructDef, fb::Definition>(m, "StructDef")
      .def(py::init<>())
      .def("__repr__",
           [](const fb::StructDef &self) {
             return "<StructDef: \"" + self.name + "\">";
           })
      .def_readonly("fields", &fb::StructDef::fields, RETPOL_REFINT)
      .def_readonly("fixed", &fb::StructDef::fixed)
      .def_readonly("predecl", &fb::StructDef::predecl)
      .def_readonly("sortbysize", &fb::StructDef::sortbysize)
      .def_readonly("has_key", &fb::StructDef::has_key)
      .def_readonly("minalign", &fb::StructDef::minalign)
      .def_readonly("bytesize", &fb::StructDef::bytesize);
  add_symbol_table<fb::StructDef>(m, "StructDef");

  // EnumVal
  py::class_<fb::EnumVal>(m, "EnumVal")
      .def(py::init<const std::string &, int64_t>())
      .def("__repr__",
           [](const fb::EnumVal &self) {
             return "<EnumVal: \"" + self.name + "\">";
           })
      .def_readonly("name", &fb::EnumVal::name)
      .def_readonly("doc_comment", &fb::EnumVal::doc_comment, RETPOL_REFINT)
      .def_readonly("value", &fb::EnumVal::value)
      .def_readonly("union_type", &fb::EnumVal::union_type);

  // EnumDef
  py::class_<fb::EnumDef, fb::Definition>(m, "EnumDef")
      .def(py::init<>())
      .def("__repr__",
           [](const fb::EnumDef &self) {
             return "<EnumDef: \"" + self.name + "\">";
           })
      .def_readonly("values", &fb::EnumDef::vals, RETPOL_REFINT)
      .def_readonly("is_union", &fb::EnumDef::is_union)
      .def_readonly("underlying_type", &fb::EnumDef::underlying_type,
                    RETPOL_REFINT);
  add_symbol_table<fb::EnumDef>(m, "EnumDef");

  // RPCCall
  // TODO

  // ServiceDef
  // TODO
  py::class_<fb::ServiceDef, fb::Definition>(m, "ServiceDef")
      .def(py::init<>())
      .def("__repr__", [](const fb::ServiceDef &self) {
        return "<ServiceDef: \"" + self.name + "\">";
      });
  add_symbol_table<fb::ServiceDef>(m, "ServiceDef");

  // Parser
  py::class_<fb::Parser>(m, "Parser", py::buffer_protocol())
      .def(py::init<>())
      .def("__repr__",
           [](const fb::Parser &self) {
             return "<Parser: " + ascii_or_hex(self.file_identifier_) + ">";
           })
      .def_readonly("error", &fb::Parser::error_, RETPOL_COPY)
      .def_readonly("root_struct_def", &fb::Parser::root_struct_def_,
                    RETPOL_REFINT)
      .def_property_readonly("file_identifier",
                             [](const fb::Parser &self) {
                               return py::bytes(self.file_identifier_);
                             })
      .def_readonly("file_extension", &fb::Parser::file_extension_)
      .def_readonly("uses_flexbuffers", &fb::Parser::uses_flexbuffers_)
      .def_readonly("included_files", &fb::Parser::included_files_, RETPOL_COPY)
      .def_readonly("files_included_per_file",
                    &fb::Parser::files_included_per_file_, RETPOL_COPY)
      .def_readonly("native_included_files",
                    &fb::Parser::native_included_files_, RETPOL_COPY)
      .def_readonly("known_attributes", &fb::Parser::known_attributes_,
                    RETPOL_COPY)

      .def_readonly("types", &fb::Parser::types_, RETPOL_REFINT)
      .def_readonly("structs", &fb::Parser::structs_, RETPOL_REFINT)
      .def_readonly("enums", &fb::Parser::enums_, RETPOL_REFINT)
      .def_readonly("services", &fb::Parser::services_, RETPOL_REFINT)
      .def_readonly("namespaces", &fb::Parser::namespaces_, RETPOL_REFINT)
      .def_readonly("current_namespace", &fb::Parser::current_namespace_,
                    RETPOL_REFINT)
      .def_readonly("empty_namespace", &fb::Parser::empty_namespace_,
                    RETPOL_REFINT)

      /*
      .def("dump_bfbs", [](fb::Parser &self) {
          if (!self.builder_.GetSize()) {
            self.Serialize();
            self.file_extension_ = reflection::SchemaExtension();
          }
          auto data = reinterpret_cast<char *>(
              self.builder_.GetBufferPointer());
          size_t size = self.builder_.GetSize();
          py::bytes bytes {data, size};
          return bytes;
          })
      */
      ;

  // Functions
  m.def("parse_file", &parse_file, RETPOL_TAKEOWN, "source_filename"_a,
        "include_paths"_a = py::list{}, "hash_identifier"_a = true);
  /*
  m.def("load_bfbs", [](py::bytes &blob) {
        auto c_blob = blob.cast<std::string>();
        bool ok;
        fb::Parser *parser = new fb::Parser {parser_options()};
        ok = parser->Deserialize(
          reinterpret_cast<const uint8_t *>(c_blob.c_str()),
          c_blob.size()
          );
        if (!ok) throw ParserError {
          "Unable to deserialize binary schema" };
        return parser;
        }, RETPOL_TAKEOWN
      );
  */

  m.def("is_scalar", [](fb::BaseType &val) { return fb::IsScalar(val); });
  m.def("is_integer", [](fb::BaseType &val) { return fb::IsInteger(val); });
  m.def("is_float", [](fb::BaseType &val) { return fb::IsFloat(val); });
  m.def("is_long", [](fb::BaseType &val) { return fb::IsLong(val); });
  m.def("is_bool", [](fb::BaseType &val) { return fb::IsBool(val); });
  m.def("is_one_byte", [](fb::BaseType &val) { return fb::IsOneByte(val); });
  m.def("size_of", [](fb::BaseType &val) { return fb::SizeOf(val); });
}
} // namespace flatboobs
