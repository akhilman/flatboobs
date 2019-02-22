# pylint: disable=missing-docstring

import subprocess


def cpp_format(src: str) -> str:
    cmd = "clang-format"
    if subprocess.run(["which", cmd], stdout=subprocess.DEVNULL).returncode:
        return src
    proc = subprocess.Popen([cmd], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, close_fds=True)
    proc.stdin.write(src.encode('utf8'))
    proc.stdin.close()

    return proc.stdout.read().decode('utf8')
