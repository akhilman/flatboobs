#define BOOST_TEST_MODULE Table with enums
#include "enums_flatboobs.hpp"
#include <boost/test/data/monomorphic.hpp>
#include <boost/test/data/test_case.hpp>
#include <boost/test/unit_test.hpp>
#include <iostream>
#include <tuple>

using namespace flatboobs::schema::test;
namespace bdata = boost::unit_test::data;

std::vector<TestEnumEnum> enum_dataset{TestEnumEnum::Bar, TestEnumEnum::Buz,
                                       TestEnumEnum::Foo};

std::vector<TestEnumFlag> flag_dataset{
    TestEnumFlag::NONE,
    TestEnumFlag::ANY,
    TestEnumFlag::Bar,
    TestEnumFlag::Buz,
    TestEnumFlag::Foo,
    TestEnumFlag::Buz | TestEnumFlag::Foo,
    TestEnumFlag::Bar | TestEnumFlag::Foo,
    TestEnumFlag::Bar | TestEnumFlag::Buz,
};

std::vector<TestEnum> dataset() {
  std::vector<TestEnum> combined{};
  for (auto enum_val : enum_dataset) {
    for (auto flag_val : flag_dataset) {
      combined.push_back({flag_val, enum_val});
    }
  }
  return combined;
}

BOOST_AUTO_TEST_CASE(test_default_values) {
  TestEnum table{};
  DefaultTestEnum default_table{};

  BOOST_TEST(table.test_enum() == default_table.test_enum());
  BOOST_TEST(table.test_flag() == default_table.test_flag());
}

BOOST_AUTO_TEST_CASE(test_flag_any_value) {
  BOOST_TEST(TestEnumFlag::ANY ==
             (TestEnumFlag::Foo | TestEnumFlag::Bar | TestEnumFlag::Buz));
  BOOST_TEST(TestEnumFlag::ANY == (~TestEnumFlag::NONE & TestEnumFlag::ANY));
}

BOOST_DATA_TEST_CASE(test_flag_string_conversion, flag_dataset) {
  std::string str{TestEnumFlag_to_string(sample)};
  TestEnumFlag result{TestEnumFlag_from_string(str)};
  BOOST_TEST(result == sample);
}

BOOST_DATA_TEST_CASE(test_enum_string_conversion, enum_dataset) {
  std::string str{TestEnumEnum_to_string(sample)};
  TestEnumEnum result{TestEnumEnum_from_string(str)};
  BOOST_TEST(result == sample);
}

BOOST_DATA_TEST_CASE(test_pack_unpack, bdata::make(dataset()), sample) {
  auto message = pack_TestEnum(sample);
  auto result = unpack_TestEnum(message);
  BOOST_TEST(result->test_enum() == sample.test_enum());
  BOOST_TEST(result->test_flag() == sample.test_flag());
  BOOST_TEST(*result == sample);
}
