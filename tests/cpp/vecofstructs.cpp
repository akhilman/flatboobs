#define BOOST_TEST_MODULE Test vector of structs
#include <boost/test/data/test_case.hpp>
#include <boost/test/unit_test.hpp>
// #include <flatboobs/utils.hpp>
#include <flatboobs_test_schema/vecofstructs.hpp>
// #include <iostream>

using namespace flatboobs::schema::test;

std::vector<TestStruct> dataset() {
  std::vector<TestStruct> samples{};
  TestStruct sample{};
  samples.push_back(sample);
  for (int i = 0; i < 10; i++) {
    sample.set_a(std::rand() % 0xff);
    sample.set_b(std::rand() / 100);
    switch (i % 3) {
    case 0:
      sample.set_e(TestEnum::Foo);
      break;
    case 1:
      sample.set_e(TestEnum::Bar);
      break;
    case 2:
      sample.set_e(TestEnum::Buz);
      break;
    }
    samples.push_back(sample);
  }
  return samples;
}

BOOST_AUTO_TEST_CASE(test_defaults) {
  TestVecOfStructs table{};
  BOOST_TEST(table.structs().size() == 0);
}

BOOST_AUTO_TEST_CASE(test_string_view) {
  auto sample = dataset();
  TestVecOfStructs table{flatboobs::Vector(sample)};
  BOOST_TEST(table.structs().str() ==
             std::string_view(reinterpret_cast<const char *>(sample.data()),
                              sample.size() * sizeof(TestStruct)));
}

BOOST_AUTO_TEST_CASE(test_pack_unpack) {
  auto sample = dataset();
  TestVecOfStructs table{};
  table = table.evolve(sample);
  auto message = flatboobs::pack(table);
  auto result = flatboobs::unpack<TestVecOfStructs>(message);
  BOOST_TEST(result.structs() == sample);
  BOOST_TEST(result == table);
  // flatboobs::hexdump(std::cout, message.str());
}
