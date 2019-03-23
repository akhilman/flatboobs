#define BOOST_TEST_MODULE Table with scalar fields
#include "scalars_flatboobs.h"
#include <boost/test/data/monomorphic.hpp>
#include <boost/test/data/test_case.hpp>
#include <boost/test/unit_test.hpp>
#include <iostream>

using namespace flatboobs::schema::test;
namespace bdata = boost::unit_test::data;

class Dataset {
public:
  struct sample {
    int8_t int_8;
    int16_t int_16;
    int32_t int_32;
    int64_t int_64;

    uint8_t uint_8;
    uint16_t uint_16;
    uint32_t uint_32;
    uint64_t uint_64;

    float float_32;
    float float_64;

    bool bool_true;
    bool bool_false;
  };

  struct iterator {
    sample value;
    iterator() { operator++(); }
    sample &operator*() { return value; }
    sample &operator++() {
      value.int_8 = (std::rand() % 200) - 100;
      value.int_16 = (std::rand() % 200) - 100;
      value.int_32 = (std::rand() % 200) - 100;
      value.int_64 = (std::rand() % 200) - 100;
      value.uint_8 = (std::rand() % 200);
      value.uint_16 = (std::rand() % 200);
      value.uint_32 = (std::rand() % 200);
      value.uint_64 = (std::rand() % 200);

      value.float_32 = (std::rand() / 1000);
      value.float_64 = (std::rand() / 1000);

      value.bool_true = (std::rand() % 2);
      value.bool_false = (std::rand() % 2);
      return value;
    }
  };

  bdata::size_t size() const { return 10; }
  iterator begin() const { return iterator(); }
};

std::ostream &operator<<(std::ostream &stream, const Dataset::sample &sample) {
  stream << +sample.int_8 << " " << sample.int_16 << " " << sample.int_32 << " "
         << sample.int_64 << " " << +sample.uint_8 << " " << sample.uint_16
         << " " << sample.uint_32 << " " << sample.uint_64 << " "
         << sample.float_32 << " " << sample.float_64 << " " << sample.bool_true
         << " " << sample.bool_false;
  return stream;
}

namespace boost {
namespace unit_test {
namespace data {
namespace monomorphic {
template <> struct is_dataset<Dataset> : boost::mpl::true_ {};
} // namespace monomorphic
} // namespace data
} // namespace unit_test
}; // namespace boost

BOOST_AUTO_TEST_CASE(test_default_values) {

  TestScalars table{};

  BOOST_TEST(table.int_8() == TestScalars::default_values::int_8());
  BOOST_TEST(table.int_16() == TestScalars::default_values::int_16());
  BOOST_TEST(table.int_32() == TestScalars::default_values::int_32());
  BOOST_TEST(table.int_64() == TestScalars::default_values::int_64());
  BOOST_TEST(table.uint_8() == TestScalars::default_values::uint_8());
  BOOST_TEST(table.uint_16() == TestScalars::default_values::uint_16());
  BOOST_TEST(table.uint_32() == TestScalars::default_values::uint_32());
  BOOST_TEST(table.uint_64() == TestScalars::default_values::uint_64());
  BOOST_TEST(table.float_32() == TestScalars::default_values::float_32());
  BOOST_TEST(table.float_64() == TestScalars::default_values::float_64());
  BOOST_TEST(table.bool_true() == TestScalars::default_values::bool_true());
  BOOST_TEST(table.bool_false() == TestScalars::default_values::bool_false());
}

BOOST_DATA_TEST_CASE(test_random_values, Dataset()) {

  TestScalars table{sample.int_8,    sample.int_16,    sample.int_32,
                    sample.int_64,   sample.uint_8,    sample.uint_16,
                    sample.uint_32,  sample.uint_64,   sample.float_32,
                    sample.float_64, sample.bool_true, sample.bool_false};

  BOOST_TEST(table.int_8() == sample.int_8);
  BOOST_TEST(table.int_16() == sample.int_16);
  BOOST_TEST(table.int_32() == sample.int_32);
  BOOST_TEST(table.int_64() == sample.int_64);

  BOOST_TEST(table.uint_8() == sample.uint_8);
  BOOST_TEST(table.uint_16() == sample.uint_16);
  BOOST_TEST(table.uint_32() == sample.uint_32);
  BOOST_TEST(table.uint_64() == sample.uint_64);

  BOOST_TEST(table.float_32() == sample.float_32);
  BOOST_TEST(table.float_64() == sample.float_64);

  BOOST_TEST(table.bool_true() == sample.bool_true);
  BOOST_TEST(table.bool_false() == sample.bool_false);
}

BOOST_DATA_TEST_CASE(test_pack_unpack, Dataset()) {

  auto source = std::make_shared<TestScalars>(
      sample.int_8, sample.int_16, sample.int_32, sample.int_64, sample.uint_8,
      sample.uint_16, sample.uint_32, sample.uint_64, sample.float_32,
      sample.float_64, sample.bool_true, sample.bool_false);
  auto data = source->pack();
  auto result = TestScalars::unpack(data);

  BOOST_TEST(result->int_8() == sample.int_8);
  BOOST_TEST(result->int_16() == sample.int_16);
  BOOST_TEST(result->int_32() == sample.int_32);
  BOOST_TEST(result->int_64() == sample.int_64);

  BOOST_TEST(result->uint_8() == sample.uint_8);
  BOOST_TEST(result->uint_16() == sample.uint_16);
  BOOST_TEST(result->uint_32() == sample.uint_32);
  BOOST_TEST(result->uint_64() == sample.uint_64);

  BOOST_TEST(result->float_32() == sample.float_32);
  BOOST_TEST(result->float_64() == sample.float_64);

  BOOST_TEST(result->bool_true() == sample.bool_true);
  BOOST_TEST(result->bool_false() == sample.bool_false);
}
