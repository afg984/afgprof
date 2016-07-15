TOOLCHAIN = arm-linux-androideabi-
CC = $(TOOLCHAIN)gcc
CFLAGS = -pie
AR = $(TOOLCHAIN)ar

a.out: main.c gmon.a
	$(CC) $(CFLAGS) -pg -g $^

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
gmon.out.txt: a.out
	adb root
	adb push a.out /data
	adb shell "/data/a.out > /data/gmon.out.txt"
	adb pull /data/gmon.out.txt

.PHONY: profile
profile: gmon.out.txt
	python3 postprocess.py
