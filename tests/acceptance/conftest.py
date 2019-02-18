import pytest

import flatboobs


@pytest.fixture
def registry():

    reg = flatboobs.Registry()
    reg.load_schema_from_package('fbtest.schema')

    return reg


@pytest.fixture
def serializer(registry):
    from flatboobs.serializers.fatboobs import FatBoobs
    return FatBoobs(registry)
