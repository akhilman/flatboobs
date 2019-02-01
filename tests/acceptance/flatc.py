from typing import Dict, Optional
from flatboobs.parser import parse
from pathlib import Path

import subprocess
import json
import tempfile


def flatc_packb(
        schema: str,
        data: Dict,
        tmp_dir: Optional[str] = None
) -> bytes:

    with tempfile.TemporaryDirectory(dir=tmp_dir) as tmp_path_str:

        tmp_path = Path(tmp_path_str)

        parsed_schema = parse(schema)
        binary_file_ext = parsed_schema.file_extension

        schema_path = tmp_path / 'schema.fbs'
        json_path = tmp_path / 'message.json'
        binary_path = tmp_path / f'message.{binary_file_ext}'

        schema_path.write_text(schema)
        with json_path.open('w') as f:
            json.dump(data, f)

        sts = subprocess.call(
            'flatc --defaults-json '
            f'-o {tmp_path} -b {schema_path} {json_path}',
            shell=True
        )

        assert not sts

        buffer = binary_path.read_bytes()

    return buffer


def flatc_unpackb(
        schema: str,
        buffer: bytes,
        tmp_dir: Optional[str] = None
) -> Dict:

    with tempfile.TemporaryDirectory(dir=tmp_dir) as tmp_path_str:

        tmp_path = Path(tmp_path_str)

        schema_path = tmp_path / 'schema.fbs'
        json_path = tmp_path / 'message.json'
        binary_path = tmp_path / 'message.bin'

        schema_path.write_text(schema)
        binary_path.write_bytes(buffer)

        sts = subprocess.call(
            'flatc --strict-json --defaults-json --json '
            f'-o {tmp_path} {schema_path} --  {binary_path}',
            shell=True
        )

        assert not sts

        with json_path.open('r') as f:
            data = json.load(f)

    return data
