#define BOOST_TEST_MODULE Table with enums
#include "enumflag_flatboobs.hpp"
#include <boost/test/data/monomorphic.hpp>
#include <boost/test/data/test_case.hpp>
#include <boost/test/unit_test.hpp>
#include <iostream>
#include <tuple>

using namespace flatboobs::schema::test;
namespace bdata = boost::unit_test::data;

std::vector<TestEnum> enum_dataset{TestEnum::Bar, TestEnum::Buz, TestEnum::Foo};

std::vector<TestFlag> flag_dataset{
    TestFlag::NONE,
    TestFlag::ANY,
    TestFlag::Bar,
    TestFlag::Buz,
    TestFlag::Foo,
    TestFlag::Buz | TestFlag::Foo,
    TestFlag::Bar | TestFlag::Foo,
    TestFlag::Bar | TestFlag::Buz,
};

std::vector<TestEnumAndFlag> dataset() {
  std::vector<TestEnumAndFlag> combined{};
  for (auto enum_val : enum_dataset) {
    for (auto flag_val : flag_dataset) {
      combined.push_back({flag_val, enum_val});
    }
  }
  return combined;
}

BOOST_AUTO_TEST_CASE(test_default_values) {
  TestEnumAndFlag table{};
  DefaultTestEnumAndFlag default_table{};

  BOOST_TEST(table.test_enum() == default_table.test_enum());
  BOOST_TEST(table.test_flag() == default_table.test_flag());
}

BOOST_AUTO_TEST_CASE(test_flag_any_value) {
  BOOST_TEST(TestFlag::ANY == (TestFlag::Foo | TestFlag::Bar | TestFlag::Buz));
  BOOST_TEST(TestFlag::ANY == (~TestFlag::NONE & TestFlag::ANY));
}

BOOST_DATA_TEST_CASE(test_flag_string_conversion, flag_dataset) {
  std::string str{TestFlag_to_string(sample)};
  TestFlag result{TestFlag_from_string(str)};
  BOOST_TEST(result == sample);
}

BOOST_DATA_TEST_CASE(test_enum_string_conversion, enum_dataset) {
  std::string str{TestEnum_to_string(sample)};
  TestEnum result{TestEnum_from_string(str)};
  BOOST_TEST(result == sample);
}

BOOST_DATA_TEST_CASE(test_pack_unpack, bdata::make(dataset()), sample) {
  auto message = pack_TestEnumAndFlag(sample);
  auto result = unpack_TestEnumAndFlag(message);
  BOOST_TEST(result->test_enum() == sample.test_enum());
  BOOST_TEST(result->test_flag() == sample.test_flag());
  BOOST_TEST(*result == sample);
}
