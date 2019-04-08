# pylint: disable=missing-docstring
from pathlib import Path
from typing import Iterable, Sequence

from flatboobs import idl  # type: ignore
from flatboobs import logging

logger = logging.getLogger()


def load_schema(
        schema_files: Sequence[Path],
        include_paths: Sequence[Path],
) -> Iterable[idl.Parser]:
    pending = set(schema_files)
    done = set()
    while pending:
        fname = pending.pop()
        logger.info("Loading schema %s", fname)
        parser = idl.parse_file(str(fname), list(map(str, include_paths)))
        root_struct_def = parser.root_struct_def

        yield (fname, parser)

        done.add(Path(root_struct_def.file))
        for inc in map(Path, parser.included_files):
            if inc in done:
                continue
            pending.add(inc)
