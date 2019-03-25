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
  using sample = TestScalarsT;

  struct iterator {
    TestScalarsT value;
    iterator() { operator++(); }
    TestScalarsT &operator*() { return value; }
    TestScalarsT &operator++() {
      value.int_8_ = (std::rand() % 200) - 100;
      value.int_16_ = (std::rand() % 200) - 100;
      value.int_32_ = (std::rand() % 200) - 100;
      value.int_64_ = (std::rand() % 200) - 100;
      value.uint_8_ = (std::rand() % 200);
      value.uint_16_ = (std::rand() % 200);
      value.uint_32_ = (std::rand() % 200);
      value.uint_64_ = (std::rand() % 200);

      value.float_32_ = (std::rand() / 1000);
      value.float_64_ = (std::rand() / 1000);

      value.bool_true_ = (std::rand() % 2);
      value.bool_false_ = (std::rand() % 2);
      return value;
    }
  };

  bdata::size_t size() const { return 10; }
  iterator begin() const { return iterator(); }
};

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

  TestScalars table{sample};

  BOOST_TEST(table.int_8() == sample.int_8_);
  BOOST_TEST(table.int_16() == sample.int_16_);
  BOOST_TEST(table.int_32() == sample.int_32_);
  BOOST_TEST(table.int_64() == sample.int_64_);

  BOOST_TEST(table.uint_8() == sample.uint_8_);
  BOOST_TEST(table.uint_16() == sample.uint_16_);
  BOOST_TEST(table.uint_32() == sample.uint_32_);
  BOOST_TEST(table.uint_64() == sample.uint_64_);

  BOOST_TEST(table.float_32() == sample.float_32_);
  BOOST_TEST(table.float_64() == sample.float_64_);

  BOOST_TEST(table.bool_true() == sample.bool_true_);
  BOOST_TEST(table.bool_false() == sample.bool_false_);
}

BOOST_DATA_TEST_CASE(test_equals, Dataset()) {

  TestScalars lhs{sample};
  TestScalars rhs{sample};
  BOOST_TEST(lhs == rhs);
}

BOOST_AUTO_TEST_CASE(test_not_equals) {

  TestScalars lhs{1, 2, 3};
  TestScalars rhs{3, 2, 1};
  BOOST_TEST(lhs != rhs);
}

BOOST_DATA_TEST_CASE(test_pack_unpack, Dataset()) {

  auto source = std::make_shared<TestScalars>(sample);
  auto data = source->pack();
  auto result = TestScalars::unpack(data);

  BOOST_TEST(result->int_8() == sample.int_8_);
  BOOST_TEST(result->int_16() == sample.int_16_);
  BOOST_TEST(result->int_32() == sample.int_32_);
  BOOST_TEST(result->int_64() == sample.int_64_);

  BOOST_TEST(result->uint_8() == sample.uint_8_);
  BOOST_TEST(result->uint_16() == sample.uint_16_);
  BOOST_TEST(result->uint_32() == sample.uint_32_);
  BOOST_TEST(result->uint_64() == sample.uint_64_);

  BOOST_TEST(result->float_32() == sample.float_32_);
  BOOST_TEST(result->float_64() == sample.float_64_);

  BOOST_TEST(result->bool_true() == sample.bool_true_);
  BOOST_TEST(result->bool_false() == sample.bool_false_);
}
