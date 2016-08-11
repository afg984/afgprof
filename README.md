afgprof
=======

Native code profiler for Android

Features
--------

* Exact call count
* Post-process tool resolves to symbol and source code line number

Prerequisites
-------------

* Go compiler
* Android toolchain (currently only gcc is supported)
* Rooted android device

Building
--------

*   gmon.a:

    In `gmon/`: `make`

*   afgprof (post-processing tool):

    `go get github.com/afg984/afgprof/cmd/afgprof`

Usage
-----

1.  Compile your android program with `-pg` and link with `gmon.a`.

2.  Prepare output directory

    ```
    adb shell mkdir -p /data/gmon
    adb shell chmod 777 /data/gmon  # so applications have write access
    ```

3.  Run the application

4.  Get the profile result

    `adb pull /data/gmon`

    The result is a directory named with your application's pid

5.  Use the post-process tool to read the profile result, it outputs JSON to stdout

    `afgprof 19212` (for example, if your pid is 19212)

    (see below for JSON format)

Command Line Options
--------------------

```
Usage: afgprof [options] DIRECTORY

  DIRECTORY
        directory to find profile data
  -addr2line string
        specify the addr2line command (default "eu-addr2line")
  -j int
        number of addr2line workers to run simultaneously (default 1)
  -objdir string
        directory to find compiled objects in (default "objects")
```

Output format
-------------

```
{
    "calls": [{
        "caller": int,  // runtime pc
        "callee": int,  // runtime pc
        "count": int,  // call count
    }],
    "index": [{
        "pc": int,  // runtime program counter
        "symbol": string,  // the name of the symbol
        "object": string,  // the object (*.so, *.out, etc) where the symbol lives in
        "offset": int,  // offset according to object
        "source_file": string,
        "line_number": string,  // line number of the source file
    }]
}
```
