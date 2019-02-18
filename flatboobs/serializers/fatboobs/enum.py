# pylint: disable=missing-docstring

import enum
import numbers
import operator as op
from functools import reduce
from typing import Type, Union

from multipledispatch import Dispatcher

from flatboobs.typing import Integer
from flatboobs.utils import remove_prefix

any_to_enum = Dispatcher(  # pylint: disable=invalid-name
    f"{__name__}.any_to_enum"
)


@any_to_enum.register(type, str)
def str_to_enum(
        enum_class: Union[Type[enum.IntEnum], Type[enum.IntFlag]],
        value: str
) -> Union[enum.IntEnum, enum.IntFlag]:

    value = remove_prefix(f'{enum_class.__name__}.', value)
    if issubclass(enum_class, enum.IntFlag):
        values = set(value.split('|'))
    else:
        values = {value}
    try:
        return reduce(
            op.or_,
            map(lambda x:  # type: ignore
                enum_class.__members__[x], values)  # type: ignore
        )
    except KeyError as exc:
        raise ValueError(
            f"Bad value for {enum_class.__name__}: "
            + ' '.join(exc.args)
        )


@any_to_enum.register(type, numbers.Integral)
def int_to_enum(
        enum_class: Union[Type[enum.IntEnum], Type[enum.IntFlag]],
        value: Integer
) -> Union[enum.IntEnum, enum.IntFlag]:
    try:
        return enum_class(value)
    except ValueError as exc:
        raise ValueError(
            f"Bad value for {enum_class.__name__}: "
            + ' '.join(exc.args)
        )
