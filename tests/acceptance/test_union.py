import pytest

from flatboobs.utils import hexdump
from flatc import flatc_packb, flatc_unpackb


@pytest.fixture
def schema_str():
    return """
namespace flatboobs.test;

table Foo {
    foo_value:byte;
}

table Bar {
    bar_value:byte;
}

union FooBar { Foo, Bar }

table Content {
    first: FooBar;
    second: FooBar;
}

root_type Content;
file_identifier "TEST";
"""


@pytest.fixture
def data():
    return {
        "first_type": "Foo",
        "first": {
            "foo_value": 10
        }
    }


def test_unpack(schema_str, data, registry, tmp_path):

    buffer = flatc_packb(schema_str, data, tmp_path)

    print('size', len(buffer))
    print(hexdump(buffer))

    table = registry.unpackb(buffer)

    from pprint import pprint
    pprint(table)
    # assert len(table) == len(data)
    # assert frozenset(table) == frozenset(data)
    # assert frozenset(table.keys()) == frozenset(data.keys())

    # for k in data.keys():
    #     if 'float' in k:
    #         assert table[k] == pytest.approx(data[k])
    #     else:
    #         assert table[k] == data[k]

    # for res, ref in zip(sorted(table.items()), sorted(data.items())):
    #     assert res[0] == ref[0]
    #     assert res[1] == pytest.approx(ref[1])


@pytest.mark.skip(reason="TODO")
def test_pack(schema_str, data, registry, tmp_path):

    table = registry.new(file_identifier='TEST')
    table = table.evolve(**data)

    buffer = table.packb()

    print('size', len(buffer))
    print(hexdump(buffer))

    res = flatc_unpackb(schema_str, buffer, tmp_path)

    for k in data.keys():
        if 'float' in k:
            assert res[k] == pytest.approx(data[k])
        else:
            assert res[k] == data[k]
