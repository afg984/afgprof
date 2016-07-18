android-gprof
=============

gprof for android

Demo
----

1. make sure android toolchain (arm-linux-androideabi-*) and adb is in PATH
2. connect to rooted android device
3. run `make profile`

Generate dot graph
------------------

`./postprocess.py gmon.out.txt a.out libshared.so --dotgraph`

Additional options

`./postprocess.py --help`

