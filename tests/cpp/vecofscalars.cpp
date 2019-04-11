#define BOOST_TEST_MODULE Test vecotrs of scalars
#include <boost/test/unit_test.hpp>
// #include <flatboobs/utils.hpp>
#include <flatboobs_test_schema/vecofscalars.hpp>
// #include <iostream>

using namespace flatboobs::schema::test;

using test_types = std::tuple<int, float, bool, TestEnum>;
using test_types_wo_bool = std::tuple<int, float, TestEnum>;

template <typename T> struct DataSet;

template <> struct DataSet<int> {
  using T = int;
  std::vector<T> a = {1, 2, 3, 4};
  std::vector<T> b = {1, 2, 1, 4};
  static constexpr char key[] = "ints";
  TestVecOfScalars evolve(const TestVecOfScalars &_table) {
    return _table.evolve(a, {}, {}, {});
  }
};

template <> struct DataSet<float> {
  using T = float;
  std::vector<T> a = {0.1, 0.2, 0.3, 0.4};
  std::vector<T> b = {0.1, 0.2, 0.1, 0.4};
  static constexpr char key[] = "floats";
  TestVecOfScalars evolve(const TestVecOfScalars &_table) {
    return _table.evolve({}, a, {}, {});
  }
};

template <> struct DataSet<bool> {
  using T = bool;
  std::vector<T> a = {true, false, true, false};
  std::vector<T> b = {true, true, false, false};
  static constexpr char key[] = "bools";
  TestVecOfScalars evolve(const TestVecOfScalars &_table) {
    return _table.evolve({}, {}, a, {});
  }
};

template <> struct DataSet<TestEnum> {
  using T = TestEnum;
  std::vector<T> a = {TestEnum::Foo, TestEnum::Bar, TestEnum::Foo,
                      TestEnum::Buz};
  std::vector<T> b = {TestEnum::Foo, TestEnum::Buz, TestEnum::Foo,
                      TestEnum::Buz};
  static constexpr char key[] = "enums";
  TestVecOfScalars evolve(const TestVecOfScalars &_table) {
    return _table.evolve({}, {}, {}, a);
  }
};

BOOST_AUTO_TEST_CASE_TEMPLATE(test_vectors, T, test_types) {

  DataSet<T> src{};

  flatboobs::ContiguousVector<T> vec_a{src.a};
  flatboobs::ContiguousVector<T> vec_b{src.b};

  BOOST_TEST(vec_a.size() == src.a.size());
  BOOST_TEST(vec_b.size() == src.b.size());

  BOOST_TEST(vec_a.front() == src.a.front());
  BOOST_TEST(vec_a.back() == src.a.back());

  BOOST_TEST(vec_a != vec_b);
  BOOST_TEST(vec_a == src.a);
  BOOST_TEST(src.a == vec_a);
  BOOST_TEST(vec_b != src.a);
  BOOST_TEST(src.b != vec_a);
}

BOOST_AUTO_TEST_CASE_TEMPLATE(test_string_view, T, test_types_wo_bool) {

  DataSet<T> src{};

  flatboobs::ContiguousVector<T> vec_a{src.a};
  flatboobs::ContiguousVector<T> vec_b{src.b};

  BOOST_TEST(vec_a.str() ==
             std::string_view(reinterpret_cast<const char *>(src.a.data()),
                              src.a.size() * sizeof(T)));
  BOOST_TEST(vec_b.str() !=
             std::string_view(reinterpret_cast<const char *>(src.a.data()),
                              src.a.size() * sizeof(T)));
}

BOOST_AUTO_TEST_CASE_TEMPLATE(test_pack_unpack, T, test_types) {

  DataSet<T> src{};

  TestVecOfScalars table{};
  table = src.evolve(table);

  auto message = flatboobs::pack(table);
  auto result = flatboobs::unpack<TestVecOfScalars>(message);
  BOOST_TEST(result == table);

  auto result_vec = std::get<flatboobs::ContiguousVector<T>>(result[src.key]);
  BOOST_TEST(result_vec == src.a);

  // std::cout << table << std::endl;
  // flatboobs::hexdump(std::cout, message.str());
}
