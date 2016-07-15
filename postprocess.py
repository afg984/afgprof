#!/usr/bin/env python3

import argparse
import bisect
import functools
import subprocess
import re


if False:
    # Show an error message on python 2
    *Please, Use = "Python 3"


mcount_pattern = re.compile(r'LR = ([a-f0-9]+) ; PC = ([a-f0-9]+)')


def get_name(symbols, offset):
    if offset is None:
        return '?'
    for (low, size), name in symbols:
        if low <= offset < low + size:
            return name
    return '?'


def main(filename):
    with open(filename) as file:
        assert next(file) == '=== start of monstartup() ===\n'

        mapping = []

        for line in file:
            if '=== end of monstartup() ===\n' == line:
                break
            addr_range, mode, *_, objname = line.split()
            if 'x' in mode and 'a.out' in objname:
                from_addr, _, to_addr = addr_range.partition('-')
                assert _
                from_addr = int(from_addr, 16)
                to_addr = int(to_addr, 16)

                mapping.append(((from_addr, to_addr), objname))

        calls = []

        for line in file:
            if line == '=== _mcleanup() invoked ===\n':
                break

            lr, pc = map(
                functools.partial(int, base=16),
                mcount_pattern.match(line).groups())

            pcloc = lrloc = None

            for (low, high), objname in mapping:
                if low <= pc < high:
                    pcloc = pc - low
                if low <= lr < high:
                    lrloc = lr - low

                calls.append((lrloc, pcloc))

        symbols = []

        with subprocess.Popen(
            ['arm-linux-androideabi-nm', '--print-size'],
            stdout=subprocess.PIPE,
            universal_newlines=True
        ) as process:
            for line in process.stdout:
                *range_, type_, name = line.split()
                if len(range_) == 2:
                    symbols.append(((int(range_[0], 16), int(range_[1], 16)), name))

        for lrloc, pcloc in calls:
            print(get_name(symbols, lrloc), '->', get_name(symbols, pcloc))



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', default='gmon.out.txt', nargs='?')

    args = parser.parse_args()

    main(**vars(args))
