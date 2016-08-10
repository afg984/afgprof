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

gmon.a:

In `gmon/`: `make`

afgprof (post-processing tool):

TODO

Usage
-----

1.  Compile your android program with -pg and link with `gmon.a`.

2.  Prepare output directory

    ```
    adb shell mkdir -p /data/gmon
    adb shell chmod 777 /data/gmon  # so applications have write access
    ```

3.  Run the application

4.  Get the profile result

    `adb pull /data/gmon`

5.  Use the post-process tool to read the profile result, it outputs JSON to stdout

    `afgprof 19212` (the value 19212 depends on your application's pid)

    (see below for JSON format)
