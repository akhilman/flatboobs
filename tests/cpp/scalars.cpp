#define BOOST_TEST_MODULE Table with scalar fields
#include <boost/test/data/monomorphic.hpp>
#include <boost/test/data/test_case.hpp>
#include <boost/test/unit_test.hpp>
#include <flatboobs_test_schema/scalars.hpp>
#include <iostream>

using namespace flatboobs::schema::test;
namespace bdata = boost::unit_test::data;

class Dataset {
public:
  using sample = TestScalars;

  struct iterator {
    TestScalars value;
    iterator() { operator++(); }
    TestScalars &operator*() { return value; }
    TestScalars &operator++() {
      value = value.evolve((std::rand() % 200) - 100, // int_8
                           (std::rand() % 200) - 100, // int_16
                           (std::rand() % 200) - 100, // int_32
                           (std::rand() % 200) - 100, // int_64
                           (std::rand() % 200),       // unit_8
                           (std::rand() % 200),       // uint_16
                           (std::rand() % 200),       // uint_32
                           (std::rand() % 200),       // uint_64

                           (std::rand() / 1000), // float_32
                           (std::rand() / 1000), // float_64

                           (std::rand() % 2), // bool_true
                           (std::rand() % 2)  // bool_false
      );
      return value;
    }
  };

  bdata::size_t size() const { return 10; }
  iterator begin() const { return iterator(); }
};

namespace boost {
namespace unit_test {
namespace data {
namespace monomorphic {
template <> struct is_dataset<Dataset> : boost::mpl::true_ {};
} // namespace monomorphic
} // namespace data
} // namespace unit_test
}; // namespace boost

BOOST_AUTO_TEST_CASE(test_default_values) {

  TestScalars table{};

  BOOST_TEST(table.int_8() == -8);
  BOOST_TEST(table.int_16() == -16);
  BOOST_TEST(table.int_32() == 0);
  BOOST_TEST(table.int_64() == 0);
  BOOST_TEST(table.uint_8() == 0);
  BOOST_TEST(table.uint_16() == 0);
  BOOST_TEST(table.uint_32() == 0);
  BOOST_TEST(table.uint_64() == 0);
  BOOST_TEST(table.float_32() == 0);
  BOOST_TEST(table.float_64() == 0);
  BOOST_TEST(table.bool_true() == true);
  BOOST_TEST(table.bool_false() == false);
}

BOOST_DATA_TEST_CASE(test_copy, Dataset()) {

  TestScalars table{sample};

  BOOST_TEST(table.int_8() == sample.int_8());
  BOOST_TEST(table.int_16() == sample.int_16());
  BOOST_TEST(table.int_32() == sample.int_32());
  BOOST_TEST(table.int_64() == sample.int_64());

  BOOST_TEST(table.uint_8() == sample.uint_8());
  BOOST_TEST(table.uint_16() == sample.uint_16());
  BOOST_TEST(table.uint_32() == sample.uint_32());
  BOOST_TEST(table.uint_64() == sample.uint_64());

  BOOST_TEST(table.float_32() == sample.float_32());
  BOOST_TEST(table.float_64() == sample.float_64());

  BOOST_TEST(table.bool_true() == sample.bool_true());
  BOOST_TEST(table.bool_false() == sample.bool_false());

  BOOST_TEST(table == sample);
}

BOOST_DATA_TEST_CASE(test_evolve, Dataset()) {

  TestScalars lhs{sample};
  TestScalars rhs{sample};
  BOOST_TEST(lhs == rhs);

  lhs = lhs.evolve({},               // int_8:byte=-8;
                   {},               // int_16:short=-16;
                   {},               // int_32:int;
                   lhs.int_64() + 1, // int_64:long;
                   {},               // uint_8:ubyte;
                   {},               // uint_16:ushort;
                   {},               // uint_32:uint;
                   {},               // uint_64:ulong;
                   {},               // float_32:float;
                   {},               // float_64:double;
                   {},               // bool_true:bool=true;
                   {}                // bool_false:bool;
  );
  BOOST_TEST(lhs != rhs);
  BOOST_TEST(lhs.int_64() - 1 == rhs.int_64());

  lhs = lhs.evolve({},               // int_8:byte=-8;
                   {},               // int_16:short=-16;
                   {},               // int_32:int;
                   lhs.int_64() - 1, // int_64:long;
                   {},               // uint_8:ubyte;
                   {},               // uint_16:ushort;
                   {},               // uint_32:uint;
                   {},               // uint_64:ulong;
                   {},               // float_32:float;
                   {},               // float_64:double;
                   {},               // bool_true:bool=true;
                   {}                // bool_false:bool;
  );
  BOOST_TEST(lhs == rhs);
}

BOOST_DATA_TEST_CASE(test_pack_unpack, Dataset()) {

  flatboobs::Data data = flatboobs::pack(sample);
  TestScalars result = flatboobs::unpack<TestScalars>(data);

  BOOST_TEST(result == sample);
}
