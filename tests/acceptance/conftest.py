import pytest

import flatboobs


@pytest.fixture(params=['fatboobs'])
def serializer(request):
    return request.param


@pytest.fixture
def registry(serializer):

    reg = flatboobs.Registry(serializer=serializer)
    reg.load_schema_from_package('fbtest.schema')

    return reg
