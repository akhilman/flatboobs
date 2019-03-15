# pylint: disable=missing-docstring

from pathlib import Path
from typing import Optional, Sequence

from jinja2 import Environment, PackageLoader, select_autoescape

from .filters import FILTERS
from .tests import TESTS


def generate(
        # pylint: disable=too-many-arguments
        project_name: str,
        schema_paths: Sequence[Path],
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

    output_file = output_dir / "CMakeLists.txt"
    template = env.get_template('CMakeLists.txt')
    flatboobs_args = []
    if rpc:
        flatboobs_args.append(f"--rpc={rpc}")
    if python:
        flatboobs_args.append("--python")
    with output_file.open('w') as output:
        output.write(template.render(
            project_name=project_name,
            output_dir=output_dir,
            schema_paths=schema_paths,
            include_paths=include_paths,
            flatboobs_args=' '.join(flatboobs_args),
        ))
