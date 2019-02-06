import pytest

from flatboobs.utils import hexdump
from flatc import flatc_packb, flatc_unpackb


@pytest.fixture
def schema_str():
    return """
namespace flatboobs.test;

table Content {
    hidden:bool (deprecated);
    int_8:byte;
    int_16:short;
    int_32:int;
    int_64:long;
    uint_8:ubyte;
    uint_16:ushort;
    uint_32:uint;
    uint_64:ulong;
    float_32:float;
    float_64:double;
    true:bool;
    false:bool;
}

root_type Content;
file_identifier "TEST";
"""


@pytest.fixture
def data():
    return {
        'int_8': -8,
        'int_16': -1616,
        'int_32': -323232,
        'int_64': -6464646464,
        'uint_8': 8,
        'uint_16': 1616,
        'uint_32': 323232,
        'uint_64': 6464646464,
        'float_32': 32e32,
        'float_64': 64e64,
        'true': True,
        'false': False,
    }


def test_unpack(schema_str, data, registry, tmp_path):

    buffer = flatc_packb(schema_str, data, tmp_path)

    print('size', len(buffer))
    print(hexdump(buffer))

    table = registry.unpackb(buffer)

    assert len(table) == len(data)
    assert frozenset(table) == frozenset(data)
    assert frozenset(table.keys()) == frozenset(data.keys())

    for k in data.keys():
        if 'float' in k:
            assert table[k] == pytest.approx(data[k])
        else:
            assert table[k] == data[k]

    for res, ref in zip(sorted(table.items()), sorted(data.items())):
        assert res[0] == ref[0]
        assert res[1] == pytest.approx(ref[1])


# @pytest.mark.skip(reason="TODO")
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
