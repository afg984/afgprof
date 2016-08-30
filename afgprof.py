#!/usr/bin/env python3

import argparse
import asyncio
import bisect
import collections
import contextlib
import functools
import json
import os
import pathlib
import re
import shlex
import shutil
import struct
import subprocess
import sys

hexint = functools.partial(int, base=16)

*'This script only works under Python 3.5 or later',


class DictObj:
    def __init__(self, obj):
        self.obj = obj

    def __getitem__(self, item):
        try:
            return getattr(self.obj, item)
        except AttributeError:
            raise KeyError(item) from None


class ProgressBar:
    def __init__(
            self,
            arg=None,
            length=None,
            *,
            format_='\r{prefix}{pi}.{pf}% ({count}/{length}){suffix}',
            prefix='',
            suffix='',
            file=sys.stderr
    ):
        if isinstance(arg, int):
            self.length = int(arg)
        else:
            if length is None:
                self.length = len(arg)
            else:
                self.length = int(length)
            self.iter = iter(arg)
        self.count = 0
        self.p = 0
        self.prefix = prefix
        self.suffix = suffix
        self.format = format_
        self.file = file
        self._dictobj = DictObj(self)
        self.print()

    def increment(self):
        self.count += 1
        nextp = 1000 * self.count // self.length
        if self.p == nextp:
            return
        self.p = nextp
        self.print()
        if self.p == 1000:
            print(file=self.file)

    @property
    def pi(self):
        return self.p // 10

    @property
    def pf(self):
        return self.p % 10

    def __len__(self):
        return self.length

    def __iter__(self):
        self.count -= 1
        return self

    def __next__(self):
        self.increment()
        return next(self.iter)

    def print(self):
        print(
            end=self.format.format_map(self._dictobj),
            file=self.file,
            flush=True,
        )


async def gather_cancel(*coros, loop):
    assert loop is not None
    tasks = [asyncio.ensure_future(coro, loop=loop) for coro in coros]
    try:
        return await asyncio.gather(*tasks, loop=loop)
    except:
        for task in tasks:
            task.cancel()
        raise


class Addr2line:
    def __init__(self, command, workers):
        if shutil.which(command) is None:
            raise Exception(
                '{} not found in PATH'.format(shlex.quote(command))
            )

        self.command = command
        if workers > 0:
            self.workers = workers
        else:
            from multiprocessing import cpu_count
            self.workers = cpu_count()

    def find_symbol_and_line(self, filename, addresses):
        self.filename = filename
        self.address_iter = iter(addresses)
        self.results = []

        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            task = gather_cancel(
                *(self._worker(i) for i in range(self.workers)),
                loop=self.loop,
            )
            self.loop.run_until_complete(task)
            return self.results
        finally:
            self.loop.close()

    async def _worker(self, i):
        process = await asyncio.create_subprocess_exec(
            self.command,
            '-f',
            '-e',
            self.filename,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            loop=self.loop
        )

        input_completed = False
        queue = asyncio.Queue(maxsize=10, loop=self.loop)

        async def input_worker():
            for address in self.address_iter:
                await queue.put(address)
                process.stdin.write('{:x}\n'.format(address).encode())
                await process.stdin.drain()
            process.stdin.write_eof()
            nonlocal input_completed
            input_completed = True

        def handle_eof():
            if process.returncode is None:
                raise EOFError
            else:
                raise Exception(
                    'Process ended unexpectedly with return code {}'.format(
                        process.returncode
                    )
                )

        async def output_worker():
            while not input_completed or queue.qsize():
                symbol = (await process.stdout.readline()).strip().decode()
                if not symbol:
                    handle_eof()
                location = (await process.stdout.readline()).strip().decode()
                if not location:
                    handle_eof()
                address = queue.get_nowait()
                self.results.append((address, symbol, location))
            await process.wait()

        try:
            await gather_cancel(
                input_worker(),
                output_worker(),
                loop=self.loop,
            )
        except:
            with contextlib.suppress(ProcessLookupError):
                process.kill()
            raise


class Region(
        collections.namedtuple(
            'Region',
            ('address', 'perms', 'offset', 'dev', 'inode', 'pathname')
        )
):

    pattern = re.compile(
        r'([0-9a-f]{1,16})-([0-9a-f]{1,16}) '
        r'([\w-]+) '
        r'([0-9a-f]{1,16}) '
        r'([0-9a-f]){2}:([0-9a-f]){2} '
        r'(\d+) '
        r'*([^\n]*)'
    )

    @classmethod
    def fromline(cls, line):
        match = cls.pattern.match(line)
        if match is None:
            raise ValueError('bad value for region pattern: {!r}'.format(line))
        addr0, addr1, perms, offset, dev, inode0, inode1, pathname = \
            match.groups()
        return cls(
            address=(hexint(addr0), hexint(addr1)),
            perms=perms,
            offset=hexint(offset),
            dev=dev,
            inode=(hexint(inode0), hexint(inode1)),
            pathname=pathname,
        )


class Map:
    def __init__(self, region_iter):
        self.regions = sorted(region_iter)

    @classmethod
    def fromfile(cls, file, executable_only=False):
        regions = map(Region.fromline, file)
        if executable_only:
            regions = (region for region in regions if 'x' in region.perms)
        return cls(regions)

    def resolve(self, address):
        index = bisect.bisect_right(self.regions, ((address, ), )) - 1
        if index < 0:
            return None
        region = self.regions[index]
        if region.address[1] <= address:
            return None
        return region

    def translate(self, address):
        resolved = self.resolve(address)
        if resolved is None:
            return None, address
        return (
            resolved.pathname, address - resolved.address[0] + resolved.offset
        )


def get_parser():
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('directory', help='directory to find calls and maps')
    parser.add_argument(
        '--addr2line',
        metavar='COMMAND',
        help='addr2line command',
        default='arm-linux-androideabi-addr2line'
    )
    parser.add_argument(
        '-j',
        metavar='N',
        help='spawn N addr2line processes. '
        'If N is less than 1, afgprof will use the number of CPUs as N',
        type=int,
        default=1
    )
    parser.add_argument(
        '--objdir',
        metavar='DIRECTORY',
        help='directory to find unstripped objects',
        default='.'
    )
    return parser


def main():
    options = get_parser().parse_args()

    addr2line = Addr2line(options.addr2line, options.j)

    objdir = pathlib.Path(options.objdir)
    directory = pathlib.Path(options.directory)

    with (directory / 'maps').open() as file:
        map_ = Map.fromfile(file)

    index = {}
    call_count = collections.Counter()

    calls_file = directory / 'calls'
    with calls_file.open(mode='rb') as file:
        data = file.read()
    length = len(data) // 16
    for lr, pc, count in ProgressBar(
            struct.iter_unpack('<IIQ', data),
            length,
            prefix='READ {}: '.format(calls_file)
    ):
        call_count[lr, pc] += count
        index[lr] = {}
        index[pc] = {}

    grouped = collections.defaultdict(dict)
    for pc, info in index.items():
        info['pathname'], info['offset'] = map_.translate(pc)
        if info['pathname'] is not None:
            grouped[info['pathname']][info['offset']] = info

    for pathname, grouped_index in grouped.items():
        objpath = objdir / os.path.basename(pathname)
        if not objpath.exists():
            print('SKIP {}: does not exist'.format(objpath), file=sys.stderr)
            continue
        for address, symbol, location in ProgressBar(
                addr2line.find_symbol_and_line(str(objpath), grouped_index),
                len(grouped_index),
                prefix='ADDR2LINE {}: '.format(objpath)
        ):
            grouped_index[address]['symbol'] = symbol
            grouped_index[address]['location'] = location

    json.dump(
        {
            'index': index,
            'calls': [
                {
                    'lr': lr,
                    'pc': pc,
                    'count': count,
                }
                for (lr, pc), count
                in call_count.most_common()
            ]
        },
        sys.stdout,
        indent=2
    )
    print()


if __name__ == '__main__':
    main()
