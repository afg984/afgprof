android-gprof
=============

gprof for android

Demo
----

1. connect to rooted android device
2. run `make profile`

Generate dot graph
------------------

`./postprocess.py gmon.out.txt a.out libshaed.so --dotgraph`

Additional options

`./postprocess.py --help`

