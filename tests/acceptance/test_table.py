import flatbuffers
import pytest

from fbtest.schema import TestTable, TestTableInnerA, TestTableInnerB
from flatboobs.utils import asnative, hexdump


@pytest.fixture
def data():
    inner_a = {
        'value_a': 0xaa,
        'value_b': 0xab,
    }
    inner_b = {
        'value_a': 0xba,
        'value_b': 0xbb,
        'value_c': 0xbc,
    }
    return {
        'inner_a': inner_a,
        'inner_a_copy': inner_a,
        'inner_b': inner_b
    }


def flatbuffers_pack(data):

    builder = flatbuffers.Builder(1024)

    TestTableInnerA.TestTableInnerAStart(builder)
    TestTableInnerA.TestTableInnerAAddValueA(
        builder, data['inner_a']['value_a'])
    TestTableInnerA.TestTableInnerAAddValueB(
        builder, data['inner_a']['value_b'])
    inner_a = TestTableInnerA.TestTableInnerAEnd(builder)

    TestTableInnerB.TestTableInnerBStart(builder)
    TestTableInnerB.TestTableInnerBAddValueA(
        builder, data['inner_b']['value_a'])
    TestTableInnerB.TestTableInnerBAddValueB(
        builder, data['inner_b']['value_b'])
    TestTableInnerB.TestTableInnerBAddValueC(
        builder, data['inner_b']['value_c'])
    inner_b = TestTableInnerB.TestTableInnerBEnd(builder)

    TestTable.TestTableStart(builder)
    TestTable.TestTableAddInnerA(builder, inner_a)
    TestTable.TestTableAddInnerACopy(builder, inner_a)
    TestTable.TestTableAddInnerB(builder, inner_b)
    root = TestTable.TestTableEnd(builder)

    builder.Finish(root)

    return builder.Output()


def flatbuffers_unpack(buffer):
    return TestTable.TestTable.GetRootAsTestTable(buffer, 0)


def test_unpack(registry, data):

    buffer = flatbuffers_pack(data)

    print('size', len(buffer))
    print(hexdump(buffer))

    table = registry.unpackb(buffer, root_type='TestTable')

    result = asnative(table)

    from pprint import pprint
    pprint(result)

    assert result.keys() == data.keys()
    for root_key in data.keys():
        assert result[root_key].keys() == data[root_key].keys()
        for inner_key in data[root_key].keys():
            assert result[root_key][inner_key] \
                == pytest.approx(data[root_key][inner_key])


# @pytest.mark.skip(reason="TODO")
def test_pack(registry, data):

    table = registry.new('TestTable', data)

    buffer = table.packb()

    print('size', len(buffer))
    print(hexdump(buffer))

    res = flatbuffers_unpack(buffer)

    assert res.InnerA().ValueA() == data['inner_a']['value_a']
    assert res.InnerA().ValueB() == data['inner_a']['value_b']

    assert res.InnerACopy().ValueA() == data['inner_a']['value_a']
    assert res.InnerACopy().ValueB() == data['inner_a']['value_b']

    assert res.InnerB().ValueA() == pytest.approx(data['inner_b']['value_a'])
    assert res.InnerB().ValueB() == pytest.approx(data['inner_b']['value_b'])
    assert res.InnerB().ValueC() == data['inner_b']['value_c']


def test_empty(registry):

    table = registry.new('TestTable')

    assert table['inner_a'] is None
    assert table['inner_b'] is None

    buffer = table.packb()

    print('size', len(buffer))
    print(hexdump(buffer))

    res = flatbuffers_unpack(buffer)

    assert res.InnerA() is None
    assert res.InnerACopy() is None
    assert res.InnerB() is None

    table = registry.unpackb(buffer, root_type='TestTable')

    assert table['inner_a'] is None
    assert table['inner_b'] is None


def test_mutation(registry, data):

    buffer = flatbuffers_pack(data)

    table = registry.unpackb(buffer, root_type='TestTable')

    table = table.evolve(
        inner_a=table['inner_a'].evolve(
            value_a=0xff
        )
    )

    assert table['inner_a']['value_a'] == 0xff
    assert table['inner_a']['value_b'] == data['inner_a']['value_b']
    assert table['inner_a_copy']['value_a'] == data['inner_a']['value_a']

    print(table)

    buffer = table.packb()

    print('size', len(buffer))
    print(hexdump(buffer))

    res = flatbuffers_unpack(buffer)

    assert res.InnerA().ValueA() == 0xff
    assert res.InnerA().ValueB() == data['inner_a']['value_b']
    assert res.InnerACopy().ValueA() == data['inner_a']['value_a']


def test_mutation_erase(registry, data):

    buffer = flatbuffers_pack(data)

    table = registry.unpackb(buffer, root_type='TestTable')

    table = table.evolve(inner_a=None, inner_b=None)

    assert table['inner_a'] is None
    assert table['inner_b'] is None
    assert table['inner_a_copy']['value_a'] == data['inner_a']['value_a']

    buffer = table.packb()

    print('size', len(buffer))
    print(hexdump(buffer))

    res = flatbuffers_unpack(buffer)

    assert res.InnerA() is None
    assert res.InnerB() is None
    assert res.InnerACopy().ValueA() == data['inner_a']['value_a']


def test_bad_mutation(registry):

    table = registry.new('TestTable')

    with pytest.raises(TypeError):
        table.evolve(inner_a="hello")

    with pytest.raises(ValueError):
        table.evolve(inner_a=registry.new('TestTableInnerB'))
