afgprof
=======

Native code profiler for Android

Features
--------

* Call count
* Post-process tool resolves to symbol and source code line number
* Dot graph tool
* Supports clang

Prerequisites
-------------

* Python 3.5 or later
* Android toolchain
* Rooted android device

Building
--------

*   gmon.a:

    In `gmon/`: `make`

Usage
-----

1.  Compile your android program or app with `-pg` and link with `gmon.a`.

    `gmon/` also contains a example

2.  Prepare output directory

    ```
    adb shell mkdir -p /data/gmon
    adb shell chmod 777 /data/gmon  # so applications have write access
    ```

3.  Run the application

4.  Get the profile result

    `adb pull /data/gmon`

    The result is a directory named with your application's pid

5.  Put your application's native binaries (*.so, *.out, etc) to the current working directory

    They are used by `afgprof.py` to resolve symbols and line numbers.

    If you want to put them elsewhere, you can specify it via the `--objdir` option.

6.  Run `afgprof.py <pid>` to read the profile result, it outputs JSON to stdout

    `afgprof.py 19212` (for example, if your pid is 19212)
    
Call Graph
----------

`afgprof.py OPTIONS | afgprof2dot.py | dot -Tsvg callgraph.svg`

Example
-------

The makefile in `gmon/` contains an example of how to build a gprof-enabled executable

```
adb shell mkdir -p /data/gmon
adb shell chmod 777 /data/gmon
cd gmon
make profile
# assuming pid is 1468
../afgprof.py gmon/1468 | ../afgprof2dot.py | dot -Tsvg -o callgraph.svg
```

To use clang:

```
make clean
make profile COMPILER=clang
```

Options
-------

see `afgprof.py --help` and `afgprof2dot.py --help`

LICENSE
-------

`afgprof2dot.py` is adapted from https://github.com/jrfonseca/gprof2dot.

`gmon/tree.h` is adapted from libbsd.

Their licenses are included at the beginning of the file.

Other code here is licensed under the MIT license.
