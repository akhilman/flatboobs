#define BOOST_TEST_MODULE Test struct field in table
#include <boost/test/data/test_case.hpp>
#include <boost/test/unit_test.hpp>
#include <flatboobs_test_schema/struct.hpp>

namespace tt = boost::test_tools;

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
  TestStruct default_struct{};
  BOOST_TEST(default_struct.a() == 10);
  BOOST_TEST(default_struct.b() == 11);
  BOOST_TEST(default_struct.e() == TestEnum::Bar);
}

BOOST_DATA_TEST_CASE(test_init_with_values, dataset()) {
  TestStruct new_struct{sample.a(), sample.b(), sample.e()};
  BOOST_TEST(new_struct == sample);
}

BOOST_AUTO_TEST_CASE(test_set_field) {
  TestStruct default_struct{};
  TestStruct another_struct{};

  BOOST_TEST(another_struct == default_struct);

  another_struct.set_a(20);
  another_struct.set_b(3.333);
  another_struct.set_e(TestEnum::Foo);

  BOOST_TEST(another_struct.a() == 20);
  BOOST_TEST(another_struct.b() == 3.333, tt::tolerance(0.001));
  BOOST_TEST(another_struct.e() == TestEnum::Foo);

  BOOST_TEST(another_struct != default_struct);
}

BOOST_DATA_TEST_CASE(test_pack_unpack, dataset()) {
  TestStructRoot source{};
  source = source.evolve(sample);
  auto message = flatboobs::pack(source);
  auto result = flatboobs::unpack<TestStructRoot>(message);
  BOOST_TEST(result.value() == sample, tt::tolerance(0.001));
  BOOST_TEST(result == source, tt::tolerance(0.001));
}
