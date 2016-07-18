#!/usr/bin/env python3

import argparse
import collections
import functools
import os
import re
import subprocess
import sys


if False:
    # Show an error message on python 2
    *Please, Use = "Python 3"


mcount_pattern = re.compile(r'LR = ([a-f0-9]+) ; PC = ([a-f0-9]+)')


int16 = functools.partial(int, base=16)


def str16(v):
    return format(v, 'x')


Map = collections.namedtuple(
    'Map',
    ('low_address', 'high_address', 'perms', 'object_name')
)


_map_pattern = re.compile(
    r'(?P<low_address>[\da-f]+)-(?P<high_address>[\da-f]+)\s+'
    r'(?P<perms>[rwxps-]{4})\s+'
    r'[\da-f]+\s+'
    r'[\da-f]{2}:[\da-f]{2}\s+'
    r'\d+\s+'
    r'(?P<object_name>.*)\s*'
)


class MapMismatch(Exception):
    pass


def tomap(line):
    match = _map_pattern.match(line)
    if match is None:
        raise MapMismatch(line)
    group = match.groupdict()
    return Map(
        low_address=int16(group['low_address']),
        high_address=int16(group['high_address']),
        perms=group['perms'],
        object_name=group['object_name']
    )


def address_to_file_offset(maps, address):
    for map_ in maps:
        if map_.low_address <= address < map_.high_address:
            return (map_.object_name, address - map_.low_address)
    return None  # just to explicit


def file_offset_to_function(symbols, file_offset):
    if file_offset is None:
        return '?', '?'
    path, offset = file_offset
    filename = os.path.basename(path)
    if filename in symbols:
        for low, size, name in symbols[filename]:
            if low <= offset < low + size:
                return filename, name
    return filename, '?'


class OneByOneWriter:

    def call(self, caller_file, caller_name, callee_file, callee_name):
        print(
            '{}@{} -> {}@{}'.format(
                caller_name, caller_file, callee_name, callee_file)
        )

    def finalize(self):
        pass


class NCallsWriter:

    def __init__(self):
        self.count = collections.Counter()

    def call(self, callee_file, callee_name, **kw):
        self.count[callee_file, callee_name] += 1

    def finalize(self):
        for (file, name), n in self.count.most_common():
            print('{}\t{}@{}'.format(n, name, file))


def symbols_from_file(filename='a.out'):
    symbols = []
    with subprocess.Popen(
        ['arm-linux-androideabi-nm', '--print-size', filename],
        stdout=subprocess.PIPE,
        universal_newlines=True
    ) as process:
        for line in process.stdout:
            *range_, type_, name = line.split()
            if len(range_) == 2:
                symbols.append(
                    (int(range_[0], 16), int(range_[1], 16), name)
                )
    return symbols


def main(filename, executables, writer_class=OneByOneWriter):
    with open(filename) as file:
        assert next(file) == '=== start of monstartup() ===\n'

        maps = []

        for line in file:
            if '=== end of monstartup() ===\n' == line:
                break
            mapline = tomap(line)
            if 'x' in mapline.perms:
                maps.append(mapline)

        calls = []

        for line in file:
            if line == '=== _mcleanup() invoked ===\n':
                break

            lr, pc = map(
                int16,
                mcount_pattern.match(line).groups())

            calls.append((
                address_to_file_offset(maps, lr),
                address_to_file_offset(maps, pc)
            ))
        else:
            assert False

        symbols = {}

        for executable in executables:
            short = os.path.basename(executable)
            if short in symbols:
                print('Warn: duplicate {!r}'.format(short), file=sys.stderr)
            symbols[short] = symbols_from_file(executable)

        writer = writer_class()

        for lrof, pcof in calls:
            kwargs = {}
            kwargs['caller_file'], kwargs['caller_name'] = \
                file_offset_to_function(symbols, lrof)
            kwargs['callee_file'], kwargs['callee_name'] = \
                file_offset_to_function(symbols, pcof)
            writer.call(**kwargs)

        writer.finalize()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'filename',
        metavar='GMONOUT',
        default='gmon.out.txt',
        nargs='?',
        help='profile output file, defaults to gmon.out.txt'
    )
    parser.add_argument(
        'executables',
        metavar='OBJECT',
        default=['a.out'],
        nargs='*',
        help='object files to find symbols in, defaults to a.out'
    )
    writer = parser.add_mutually_exclusive_group()
    writer.add_argument(
        '--one-by-one',
        dest='writer_class',
        default=OneByOneWriter,
        help='print caller-callee pairs one by one (default)',
        action='store_const',
        const=OneByOneWriter
    )
    writer.add_argument(
        '--ncalls',
        dest='writer_class',
        help='print called functions sorted by number of calls',
        action='store_const',
        const=NCallsWriter
    )

    args = parser.parse_args()

    main(**vars(args))
