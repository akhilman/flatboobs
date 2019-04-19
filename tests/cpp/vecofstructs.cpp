#define BOOST_TEST_MODULE Test vector of structs
#include <boost/test/data/test_case.hpp>
#include <boost/test/unit_test.hpp>
// #include <flatboobs/utils.hpp>
#include <flatboobs_test_schema/vecofstructs.hpp>
// #include <iostream>

using namespace flatboobs::schema::test;

std::vector<flatboobs::Vector<TestStruct>> dataset() {
  std::vector<flatboobs::Vector<TestStruct>> samples{};
  std::vector<TestStruct> items{};
  samples.push_back({});
  for (int n = 0; n < 10; n++) {
    for (int i = 0; i < 10; i++) {
      TestStruct item{};
      items.push_back(item);
      item.set_a(std::rand() % 0xff);
      item.set_b(std::rand() / 100);
      switch (n + i % 3) {
      case 0:
        item.set_e(TestEnum::Foo);
        break;
      case 1:
        item.set_e(TestEnum::Bar);
        break;
      case 2:
        item.set_e(TestEnum::Buz);
        break;
      }
      items.push_back(item);
    }
    samples.push_back(items);
    items.clear();
  }
  return samples;
}

BOOST_AUTO_TEST_CASE(test_defaults) {
  TestVecOfStructs table{};
  BOOST_TEST(table.structs().size() == 0);
}

BOOST_DATA_TEST_CASE(test_string_view, dataset()) {
  TestVecOfStructs table{flatboobs::Vector(sample)};
  BOOST_TEST(table.structs().str() ==
             std::string_view(reinterpret_cast<const char *>(sample.data()),
                              sample.size() * sizeof(TestStruct)));
}

BOOST_DATA_TEST_CASE(test_pack_unpack, dataset()) {
  TestVecOfStructs table{};
  table = table.evolve(sample);
  auto message = flatboobs::pack(table);
  auto result = flatboobs::unpack<TestVecOfStructs>(message);
  BOOST_TEST(result.structs() == sample);
  BOOST_TEST(result == table);
  // flatboobs::hexdump(std::cout, message.str());
}
