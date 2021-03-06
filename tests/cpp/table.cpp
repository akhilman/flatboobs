#define BOOST_TEST_MODULE Test table field in table
#include <boost/test/data/test_case.hpp>
#include <boost/test/unit_test.hpp>
#include <flatboobs_test_schema/table.hpp>

namespace tt = boost::test_tools;

using namespace flatboobs::schema::test;

std::vector<TestTable> dataset() {
  std::vector<TestTable> samples{};
  TestTable sample{};
  samples.push_back(sample);

  uint8_t a;
  float b;
  TestEnum e;

  for (int i = 0; i < 10; i++) {
    a = std::rand() % 0xff;
    b = std::rand() / 100;
    switch (i % 3) {
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
    sample = sample.evolve(a, b, e);
    samples.push_back(sample);
  }
  return samples;
}

BOOST_AUTO_TEST_CASE(test_defaults) {
  TestTableRoot default_table{};
  BOOST_TEST(default_table.value().a() == 10);
  BOOST_TEST(default_table.value().b() == 11);
  BOOST_TEST(default_table.value().e() == TestEnum::Bar);
}

BOOST_DATA_TEST_CASE(test_init_with_values, dataset()) {
  TestTable new_table{sample.a(), sample.b(), sample.e()};
  BOOST_TEST(new_table == sample);
}

BOOST_DATA_TEST_CASE(test_evolve, dataset()) {
  TestTable new_table{};
  new_table = new_table.evolve(sample.a(), sample.a(), {});
  BOOST_TEST(new_table.a() == new_table.b(), tt::tolerance(0.001));
  BOOST_TEST(new_table != sample);
  new_table = new_table.evolve(sample.a(), sample.b(), sample.e());
  BOOST_TEST(new_table == sample);
}

BOOST_DATA_TEST_CASE(test_pack_unpack, dataset()) {
  TestTableRoot source{};
  source = source.evolve(sample);
  auto message = flatboobs::pack(source);
  auto result = flatboobs::unpack<TestTableRoot>(message);
  BOOST_TEST(result.value() == sample, tt::tolerance(0.001));
  BOOST_TEST(result == source, tt::tolerance(0.001));
}

BOOST_DATA_TEST_CASE(test_repack, dataset()) {

  TestTableRoot source_a{};
  auto message_a = flatboobs::pack(source_a);
  auto result_a = flatboobs::unpack<TestTableRoot>(message_a);

  auto source_b = result_a.evolve(sample);
  auto message_b = flatboobs::pack(source_b);
  auto result_b = flatboobs::unpack<TestTableRoot>(message_b);

  auto message_c = flatboobs::pack(result_b);
  auto result_c = flatboobs::unpack<TestTableRoot>(message_c);

  BOOST_TEST(message_b.data() != message_a.data());
  BOOST_TEST(message_c.data() == message_b.data());
}
