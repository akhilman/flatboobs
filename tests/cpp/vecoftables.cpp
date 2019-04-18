#define BOOST_TEST_MODULE Test vector of tables
#include <boost/test/data/test_case.hpp>
#include <boost/test/unit_test.hpp>
// #include <flatboobs/utils.hpp>
#include <flatboobs_test_schema/vecoftables.hpp>
// #include <iostream>

using namespace flatboobs::schema::test;

std::vector<flatboobs::Vector<TestTable>> dataset() {
  std::vector<flatboobs::Vector<TestTable>> samples{};
  std::vector<TestTable> items{};
  samples.push_back({});
  for (int n = 0; n < 10; n++) {
    TestTable item{};
    items.push_back(item);
    uint8_t a;
    float b;
    TestEnum e;
    for (int i = 0; i < 10; i++) {
      a = std::rand() % 0xff;
      b = std::rand() / 100;
      switch (n + i % 3) {
      case 0:
        e = TestEnum::Foo;
        break;
      case 1:
        e = TestEnum::Bar;
        break;
      case 2:
        e = TestEnum::Buz;
        break;
      }
      items.push_back(item.evolve(a, b, e));
    }
    samples.push_back(items);
    items.clear();
  }
  return samples;
}

BOOST_AUTO_TEST_CASE(test_defaults) {
  TestVecOfTables table{};
  BOOST_TEST(table.tables().size() == 0);
}

BOOST_DATA_TEST_CASE(test_pack_unpack, dataset()) {
  TestVecOfTables table{};
  table = table.evolve(sample);
  auto message = flatboobs::pack(table);
  auto result = flatboobs::unpack<TestVecOfTables>(message);
  BOOST_TEST(result.tables() == sample);
  BOOST_TEST(result == table);
  /// flatboobs::hexdump(std::cout, message.str());
}
