#define BOOST_TEST_MODULE Table with scalar fields
#include "scalars_flatboobs.hpp"
#include <boost/test/data/monomorphic.hpp>
#include <boost/test/data/test_case.hpp>
#include <boost/test/unit_test.hpp>
#include <iostream>

using namespace flatboobs::schema::test;
namespace bdata = boost::unit_test::data;

class Dataset {
public:
  using sample = TestScalars;

  struct iterator {
    TestScalars value;
    iterator() { operator++(); }
    TestScalars &operator*() { return value; }
    TestScalars &operator++() {
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

  BOOST_TEST(table.int_8() == -8);
  BOOST_TEST(table.int_16() == -16);
  BOOST_TEST(table.int_32() == 0);
  BOOST_TEST(table.int_64() == 0);
  BOOST_TEST(table.uint_8() == 0);
  BOOST_TEST(table.uint_16() == 0);
  BOOST_TEST(table.uint_32() == 0);
  BOOST_TEST(table.uint_64() == 0);
  BOOST_TEST(table.float_32() == 0);
  BOOST_TEST(table.float_64() == 0);
  BOOST_TEST(table.bool_true() == true);
  BOOST_TEST(table.bool_false() == false);
}

BOOST_AUTO_TEST_CASE(test_default_table) {

  DefaultTestScalars default_table{};

  BOOST_TEST(default_table.int_8() == -8);
  BOOST_TEST(default_table.int_16() == -16);
  BOOST_TEST(default_table.int_32() == 0);
  BOOST_TEST(default_table.int_64() == 0);
  BOOST_TEST(default_table.uint_8() == 0);
  BOOST_TEST(default_table.uint_16() == 0);
  BOOST_TEST(default_table.uint_32() == 0);
  BOOST_TEST(default_table.uint_64() == 0);
  BOOST_TEST(default_table.float_32() == 0);
  BOOST_TEST(default_table.float_64() == 0);
  BOOST_TEST(default_table.bool_true() == true);
  BOOST_TEST(default_table.bool_false() == false);
}

BOOST_DATA_TEST_CASE(test_equals, Dataset()) {

  TestScalars lhs{sample};
  TestScalars rhs{sample};
  BOOST_TEST(lhs == rhs);
  rhs.set_int_64(rhs.int_64() + 1);
  BOOST_TEST(lhs != rhs);
}

BOOST_DATA_TEST_CASE(test_random_values, Dataset()) {

  std::shared_ptr<ITestScalars> table{std::make_shared<TestScalars>(sample)};

  BOOST_TEST(table->int_8() == sample.int_8());
  BOOST_TEST(table->int_16() == sample.int_16());
  BOOST_TEST(table->int_32() == sample.int_32());
  BOOST_TEST(table->int_64() == sample.int_64());

  BOOST_TEST(table->uint_8() == sample.uint_8());
  BOOST_TEST(table->uint_16() == sample.uint_16());
  BOOST_TEST(table->uint_32() == sample.uint_32());
  BOOST_TEST(table->uint_64() == sample.uint_64());

  BOOST_TEST(table->float_32() == sample.float_32());
  BOOST_TEST(table->float_64() == sample.float_64());

  BOOST_TEST(table->bool_true() == sample.bool_true());
  BOOST_TEST(table->bool_false() == sample.bool_false());

  BOOST_TEST(*table == sample);
}

BOOST_DATA_TEST_CASE(test_pack_unpack, Dataset()) {

  auto data = pack_TestScalars(sample);
  auto result = unpack_TestScalars(data);

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

  BOOST_TEST(*result == sample);
}
