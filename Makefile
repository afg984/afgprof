TOOLCHAIN = arm-linux-androideabi-
CC = $(TOOLCHAIN)gcc
CFLAGS = -pie
AR = $(TOOLCHAIN)ar

a.out: main.c gmon.a libshared.so
	$(CC) $(CFLAGS) -pg $^ -L. -lshared

libshared.so: shared.c
	$(CC) $(CFLAGS) -pg -shared $^ -o $@

.PHONY: clean
clean:
	rm -f $(wildcard *.a *.o a.out gprof.out.txt)

mcount.o: mcount.s
	$(CC) $(CFLAGS) -c $^

gmon.o: gmon.c
	$(CC) $(CFLAGS) -c $^

gmon.a: gmon.o mcount.o
	$(AR) r $@ $^

.PHONY: gmon.out.txt
gmon.out.txt: a.out libshared.so
	adb root
	adb shell rm -f /data/gmon.out.txt
	adb push a.out /data
	adb push libshared.so /data
	adb shell "LD_LIBRARY_PATH=/data /data/a.out"
	adb pull /data/gmon.out.txt

.PHONY: profile
profile: gmon.out.txt
	./postprocess.py gmon.out.txt a.out libshared.so
