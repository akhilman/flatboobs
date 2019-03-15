# pylint: disable=missing-docstring

from pathlib import Path
from typing import Optional, Sequence, Set

from jinja2 import Environment, PackageLoader, select_autoescape

from flatboobs import idl  # type: ignore

from .cpp_format import cpp_format
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
    output_file = (
        output_dir
        / f'{(root_fname.stem)}_generated_l.h'
    )
    template = env.get_template('lazy.h/main.txt')
    with output_file.open('w') as out:
        out.write(
            cpp_format(
                template.render(
                    parser=parser,
                    output_file=output_file,
                )
            )
        )


def gen_implementation(
        env: Environment,
        parser: idl.Parser,
        output_dir: Path,
) -> None:
    root_struct_def = parser.root_struct_def
    root_fname = Path(root_struct_def.file)
    output_file = (
        output_dir
        / f'{(root_fname.stem)}_generated_l.cpp'
    )

    template = env.get_template('lazy.cpp/main.txt')
    with output_file.open('w') as out:
        out.write(
            cpp_format(
                template.render(
                    parser=parser,
                    output_file=output_file,
                )
            )
        )


def gen_module(
        env: Environment,
        parser: idl.Parser,
        output_dir: Path,
) -> None:
    root_struct_def = parser.root_struct_def
    root_fname = Path(root_struct_def.file)
    output_file = (
        output_dir
        / f'{(root_fname.stem)}.cpp'
    )

    template = env.get_template('serializer.mod/main.txt')
    with output_file.open('w') as out:
        out.write(
            cpp_format(
                template.render(
                    parser=parser,
                    output_file=output_file,
                )
            )
        )


def generate(
        schema_files: Sequence[Path],
        include_paths: Sequence[Path],
        output_dir: Path,
        rpc: Optional[str] = None,
        python: bool = False,
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
        if python:
            gen_module(env, parser, output_dir)
        if rpc:
            # TODO
            pass

        done.add(Path(root_struct_def.file))
        for inc in map(Path, parser.included_files):
            if inc in done:
                continue
            paths = set([Path(fname).parent]) | set(include_paths)
            pending.add(search_included(inc, paths))
