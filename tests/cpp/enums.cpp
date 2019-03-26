#define BOOST_TEST_MODULE Table with enums
#include "enums_flatboobs.hpp"
#include <boost/test/unit_test.hpp>
#include <iostream>

using namespace flatboobs::schema::test;

BOOST_AUTO_TEST_CASE(test_default_values) {
  TestEnum table{};

  BOOST_TEST(table.test_enum() == TestEnum::default_values::test_enum());
  BOOST_TEST(table.test_flag() == TestEnum::default_values::test_flag());
}

BOOST_AUTO_TEST_CASE(test_flags) {
  TestEnum table{TestEnumFlag::Bar | TestEnumFlag::Buz, TestEnumEnum::Foo};

  std::cout << table << std::endl;
}
