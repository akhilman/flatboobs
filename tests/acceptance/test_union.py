import enum

import flatbuffers
import pytest

from fbtest.schema import (
    TestUnion,
    TestUnionBar,
    TestUnionFoo,
    TestUnionFooBar
)
from flatboobs.utils import hexdump

data_variants = [
    {
        "foobar_type": TestUnionFooBar.TestUnionFooBar.NONE,
        "foobar": None
    },
    {
        "foobar_type": TestUnionFooBar.TestUnionFooBar.TestUnionFoo,
        "foobar": {
            "foo_value": 10
        }
    },
    {
        "foobar_type": TestUnionFooBar.TestUnionFooBar.TestUnionBar,
        "foobar": {
            "bar_value_a": 0xFFFFFFFF,
            "bar_value_b": 0xFFAAFFAA
        }
    },
]


def flatbuffers_pack(data):

    builder = flatbuffers.Builder(1024)

    if data['foobar_type'] == TestUnionFooBar.TestUnionFooBar.NONE:
        foobar = 0
    elif data['foobar_type'] == TestUnionFooBar.TestUnionFooBar.TestUnionFoo:
        TestUnionFoo.TestUnionFooStart(builder)
        TestUnionFoo.TestUnionFooAddFooValue(
            builder, data['foobar']['foo_value'])
        foobar = TestUnionFoo.TestUnionFooEnd(builder)
    elif data['foobar_type'] == TestUnionFooBar.TestUnionFooBar.TestUnionBar:
        TestUnionBar.TestUnionBarStart(builder)
        TestUnionBar.TestUnionBarAddBarValueA(
            builder, data['foobar']['bar_value_a'])
        TestUnionBar.TestUnionBarAddBarValueB(
            builder, data['foobar']['bar_value_b'])
        foobar = TestUnionBar.TestUnionBarEnd(builder)
    else:
        raise RuntimeError

    TestUnion.TestUnionStart(builder)
    if foobar:
        TestUnion.TestUnionAddFoobarType(builder, data['foobar_type'])
        TestUnion.TestUnionAddFoobar(builder, foobar)
    root = TestUnion.TestUnionEnd(builder)

    builder.Finish(root)

    return builder.Output()


def flatbuffers_unpack(buffer):
    return TestUnion.TestUnion.GetRootAsTestUnion(buffer, 0)


@pytest.mark.parametrize("data", data_variants)
def test_unpack(serializer, data):

    buffer = flatbuffers_pack(data)

    print('size', len(buffer))
    print(hexdump(buffer))

    table = serializer.unpackb('TestUnion', buffer)

    from pprint import pprint
    pprint(table)
    assert len(table) == len(data)
    assert table.keys() == data.keys()
    assert table['foobar_type'] == data['foobar_type']
    assert isinstance(table['foobar_type'], enum.IntEnum)
    if data['foobar']:
        assert dict(table['foobar']) == data['foobar']
    else:
        assert not table['foobar']


@pytest.mark.parametrize("data", data_variants)
def test_pack(serializer, data):

    buffer = serializer.packb('TestUnion', data)

    print('size', len(buffer))
    print(hexdump(buffer))

    res = flatbuffers_unpack(buffer)

    union_type = res.FoobarType()
    assert union_type == data['foobar_type']

    if data['foobar']:

        if union_type == TestUnionFooBar.TestUnionFooBar.TestUnionFoo:
            union_value_class = TestUnionFoo.TestUnionFoo
        elif union_type == TestUnionFooBar.TestUnionFooBar.TestUnionBar:
            union_value_class = TestUnionBar.TestUnionBar

        for key in data['foobar'].keys():
            foobar = union_value_class()
            foobar.Init(res.Foobar().Bytes, res.Foobar().Pos)
            getter = ''.join(x.capitalize() or '_' for x in key.split('_'))
            assert getattr(foobar, getter)() == data['foobar'][key]
    else:
        assert res.Foobar() is None


def test_evolve_with_table(serializer):

    table = serializer.new('TestUnion')
    bar = serializer.new('TestUnionBar')

    assert table['foobar_type'] == 0
    assert table['foobar_type'].name == 'NONE'

    table = table.evolve(foobar=bar)

    assert table['foobar'] == bar
    assert table['foobar_type'].name == 'TestUnionBar'


def test_evolve_with_dict(serializer):

    enum_class = serializer.registry.type_by_name('TestUnionFooBar').asenum()

    table = serializer.new('TestUnion')
    table = table.evolve(
        foobar_type='TestUnionFoo',
        foobar={'foo_value': 2}
    )

    assert table['foobar_type'] == enum_class.TestUnionFoo
    assert table['foobar_type'].name == 'TestUnionFoo'
    assert table['foobar']['foo_value'] == 2


def test_bad_evolution(serializer):

    table = serializer.new('TestUnion')
    foo = serializer.new('TestUnionFoo')

    with pytest.raises(ValueError):
        serializer.new('TestUnion', {'foobar': table})

    with pytest.raises(ValueError):
        table.evolve(
            foobar_type='TestUnionBar',
            foobar=foo
        )

    with pytest.raises(ValueError):
        table.evolve(
            foobar={'foo_value': 2}
        )
