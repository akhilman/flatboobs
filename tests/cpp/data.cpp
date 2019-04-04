#define BOOST_TEST_MODULE Test data wrapper
#include <algorithm>
#include <boost/test/data/test_case.hpp>
#include <boost/test/unit_test.hpp>
#include <flatboobs/flatboobs.hpp>
#include <iostream>
#include <vector>

#define TEST_STRING "Hello world"

static std::string static_str{TEST_STRING};

std::vector<flatboobs::Data> sample_variants() {
  std::string str{TEST_STRING};
  std::vector<flatboobs::Data> samples;
  samples.push_back(str);
  samples.push_back(&static_str);

  std::vector<uint8_t> vec;
  std::for_each(str.begin(), str.end(),
                [&vec](char chr) { vec.push_back(chr); });
  samples.push_back(vec);

  return samples;
}

BOOST_DATA_TEST_CASE(test_size, sample_variants()) {
  std::string str{TEST_STRING};

  BOOST_TEST(str.size() == sample.size());
}

BOOST_DATA_TEST_CASE(test_iterator, sample_variants()) {
  std::string str{TEST_STRING};
  BOOST_TEST(
      std::equal(sample.begin(), sample.end(), str.begin(),
                 [](auto &lhs, auto &rhs) { return int(lhs) == int(rhs); }));
}

BOOST_DATA_TEST_CASE(test_rev_iterator, sample_variants()) {
  std::string str{TEST_STRING};
  BOOST_TEST(
      std::equal(sample.rbegin(), sample.rend(), str.rbegin(),
                 [](auto &lhs, auto &rhs) { return int(lhs) == int(rhs); }));
}

BOOST_AUTO_TEST_CASE(test_multibyte_items) {
  const std::vector<uint64_t> vec{1, 2, 3, 4};
  std::string_view view{reinterpret_cast<const char *>(vec.data()),
                        vec.size() * sizeof(double)};
  flatboobs::Data data{vec};
  BOOST_TEST(data.str() == view);
}
