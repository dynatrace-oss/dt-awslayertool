# Copyright 2021 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import shlex
import shutil
import subprocess
import sys
from pathlib import PurePath

# join_args and runsubprocess are based on code
#
#   Copyright The OpenTelemetry Authors
#
# (under the same Apache 2 license)


def join_args(arglist):
    return " ".join(map(shlex.quote, arglist))


def runsubprocess(params, *args, **kwargs):
    cmdstr = join_args(params)

    # Py < 3.6 compat.
    cwd = kwargs.get("cwd")
    if cwd and isinstance(cwd, PurePath):
        kwargs["cwd"] = str(cwd)

    check = kwargs.pop("check", True)

    print(">>>", cmdstr, file=sys.stderr, flush=True)

    # This is a workaround for subprocess.run(['python']) leaving the virtualenv on Win32.
    # The cause for this is that when running the python.exe in a virtualenv,
    # the wrapper executable launches the global python as a subprocess and the search sequence
    # for CreateProcessW which subprocess.run and Popen use is a follows
    # (https://docs.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw):
    # > 1. The directory from which the application loaded.
    # This will be the directory of the global python.exe, not the venv directory, due to the suprocess mechanism.
    # > 6. The directories that are listed in the PATH environment variable.
    # Only this would find the "correct" python.exe.

    params = list(params)
    executable = shutil.which(params[0])
    if executable:
        params[0] = executable
    try:
        return subprocess.run(params, *args, check=check, **kwargs)
    except OSError as exc:
        raise ValueError("Failed executing " + repr(params) + ": " + str(exc)) from exc


def main():
    runsubprocess(("black", "."))
    runsubprocess(("isort", "."))
    runsubprocess(("flake8", "."))
    runsubprocess(("pylint", "./tests", "./src", "./scripts"))
    runsubprocess(("pytest", "./tests"))
    runsubprocess(("pip", "wheel", "--no-deps", "."))
    runsubprocess(("twine", "check", "*.whl"))


if __name__ == "__main__":
    main()
