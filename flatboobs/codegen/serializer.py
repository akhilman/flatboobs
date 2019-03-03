# pylint: disable=missing-docstring

from pathlib import Path
from typing import Sequence, Set

from jinja2 import Environment, PackageLoader, select_autoescape

from flatboobs import idl  # type: ignore

from .filters import FILTERS
from .tests import TESTS


def search_included(
        fname: Path,
        include_paths: Set[Path]
) -> Path:
    print('inc', fname, include_paths)
    raise NotImplementedError


def gen_header(
        env: Environment,
        parser: idl.Parser,
        output_dir: Path,
) -> None:
    root_struct_def = parser.root_struct_def
    root_fname = Path(root_struct_def.file)
    out_fname = (
        output_dir
        / f'{(root_fname.stem)}_generated_py.h'
    )
    template = env.get_template('serializer.h/main.txt')
    with out_fname.open('w') as out:
        out.write(template.render(
            parser=parser,
            output_file=out_fname,
        ))


def gen_implementation(
        env: Environment,
        parser: idl.Parser,
        output_dir: Path,
) -> None:
    root_struct_def = parser.root_struct_def
    root_fname = Path(root_struct_def.file)
    out_fname = (
        output_dir
        / f'{(root_fname.stem)}_generated_py.cc'
    )

    template = env.get_template('serializer.cc/main.txt')
    with out_fname.open('w') as out:
        out.write(template.render(
            parser=parser,
            output_file=out_fname,
        ))


def gen_module(
        env: Environment,
        parser: idl.Parser,
        output_dir: Path,
) -> None:
    root_struct_def = parser.root_struct_def
    root_fname = Path(root_struct_def.file)
    out_fname = (
        output_dir
        / f'{(root_fname.stem)}.cc'
    )

    template = env.get_template('serializer.mod/main.txt')
    with out_fname.open('w') as out:
        out.write(template.render(
            parser=parser,
            output_file=out_fname,
        ))


def generate(
        schema_files: Sequence[Path],
        include_paths: Sequence[Path],
        output_dir: Path,
) -> None:

    env = Environment(
        loader=PackageLoader('flatboobs', 'templates'),
        autoescape=select_autoescape(['cpp']),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(FILTERS)
    env.tests.update(TESTS)
    env.globals = {
        'BaseType': idl.BaseType,
    }

    pending = set(schema_files)
    done = set()
    while pending:
        fname = pending.pop()
        parser = idl.parse_file(str(fname), list(map(str, include_paths)))
        root_struct_def = parser.root_struct_def

        gen_header(env, parser, output_dir)
        gen_implementation(env, parser, output_dir)
        gen_module(env, parser, output_dir)

        done.add(Path(root_struct_def.file))
        for inc in map(Path, parser.included_files):
            if inc in done:
                continue
            paths = set([Path(fname).parent]) | set(include_paths)
            pending.add(search_included(inc, paths))
