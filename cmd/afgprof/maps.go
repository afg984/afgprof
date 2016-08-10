package main

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

type Address [2]uint64

type Device [2]uint16

type Region struct {
	Address  Address
	Perms    string
	Offset   uint64
	Dev      Device
	Inode    uint64
	Pathname string
}

type ObjectOffset struct {
	Pathname string
	Offset   uint64
}

type Map []Region

var RegionPat = regexp.MustCompile(`` +
	`([0-9a-f]{1,16})-([0-9a-f]{1,16}) ` +
	`([\w-]+) ` +
	`([0-9a-f]{1,16}) ` +
	`([0-9a-f]){2}:([0-9a-f]){2} ` +
	`(\d+) ` +
	`*([^\n]*)`)

func (r *Region) IsExecutable() bool {
	return strings.Contains(r.Perms, "x")
}

func (m Map) Resolve(address uint64) *Region {
	after := func(i int) bool {
		return m[i].Address[0] > address
	}
	index := sort.Search(len(m), after) - 1
	if index < 0 {
		return nil
	}

	r := &m[index]
	if r.Address[1] <= address {
		return nil
	}
	return r
}

func (m Map) Translate(address uint64) *ObjectOffset {
	resolved := m.Resolve(address)
	if resolved == nil {
		return nil
	}
	return &ObjectOffset{
		resolved.Pathname,
		address - resolved.Address[0] + resolved.Offset,
	}
}

func mustParseUint(s string, base int, bitSize int) uint64 {
	n, err := strconv.ParseUint(s, base, bitSize)
	if err != nil {
		panic(err)
	}
	return n
}

func ParseMapLine(line string) (Region, error) {
	match := RegionPat.FindStringSubmatch(line)
	if match == nil {
		return Region{}, errors.New(fmt.Sprintf("cannot parse string %q", line))
	}
	return Region{
		Address: Address{
			mustParseUint(match[1], 16, 64),
			mustParseUint(match[2], 16, 64),
		},
		Perms:  match[3],
		Offset: mustParseUint(match[4], 16, 64),
		Dev: Device{
			uint16(mustParseUint(match[5], 16, 16)),
			uint16(mustParseUint(match[6], 16, 16)),
		},
		Inode:    mustParseUint(match[7], 10, 64),
		Pathname: match[8],
	}, nil
}

func parseMap(path string, perdicate func(*Region) bool) (Map, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	reader := bufio.NewReader(file)
	result := make(Map, 0)
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				return result, nil
			}
		}
		region, err := ParseMapLine(line)
		if err != nil {
			return result, err
		}
		if perdicate(&region) {
			result = append(result, region)
		}
	}
}

func ParseMap(path string) (Map, error) {
	return parseMap(path, func(*Region) bool { return true })
}

func ParseMapX(path string) (Map, error) {
	return parseMap(path, func(r *Region) bool { return r.IsExecutable() })
}
