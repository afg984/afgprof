package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"path"
	"sort"
)

func check(e error) {
	if e != nil {
		panic(e)
	}
}

type DebugInfo struct {
	PC     uint64 `json:"pc"`
	Object string `json:"object"`
	Offset uint64 `json:"offset"`
	Symbol string `json:"symbol"`
	Source string `json:"source_file"`
	Line   string `json:"line_number"`
}

type Index struct {
	data      []*DebugInfo
	PCMap     map[uint64]*DebugInfo
	ObjectMap map[string]map[uint64]*DebugInfo
}

func (self *Index) New(pc uint64, object string, offset uint64) {
	if self.PCMap[pc] == nil {
		debinf := &DebugInfo{
			PC:     pc,
			Object: object,
			Offset: offset,
		}
		self.data = append(self.data, debinf)
		self.PCMap[pc] = debinf
		if self.ObjectMap[object] == nil {
			self.ObjectMap[object] = make(map[uint64]*DebugInfo)
		}
		self.ObjectMap[object][offset] = debinf
	}
}

func NewIndex() Index {
	return Index{
		PCMap:     make(map[uint64]*DebugInfo),
		ObjectMap: make(map[string]map[uint64]*DebugInfo),
	}
}

type DumpCall struct {
	UnmappedCall
	Count uint64 `json:"count"`
}

type ByCallCount []DumpCall

func (p ByCallCount) Len() int           { return len(p) }
func (p ByCallCount) Less(i, j int) bool { return p[i].Count > p[j].Count }
func (p ByCallCount) Swap(i, j int)      { p[i], p[j] = p[j], p[i] }

func Dump(writer io.Writer, acc *map[UnmappedCall]uint64, index *Index) {
	outgoing := struct {
		Calls []DumpCall   `json:"calls"`
		Index []*DebugInfo `json:"index"`
	}{Index: index.data}
	for call, count := range *acc {
		outgoing.Calls = append(outgoing.Calls, DumpCall{call, count})
	}
	sort.Sort(ByCallCount(outgoing.Calls))
	check(json.NewEncoder(writer).Encode(outgoing))
}

type ByPC []*DebugInfo

func (p ByPC) Len() int           { return len(p) }
func (p ByPC) Less(i, j int) bool { return p[i].PC < p[j].PC }
func (p ByPC) Swap(i, j int)      { p[i], p[j] = p[j], p[i] }

var concurrency = flag.Int("j", 1, "number of addr2line workers to run simultaneously")
var object_directory = flag.String("objdir", "objects", "directory to find compiled objects in")

func Usage() {
	fmt.Fprintf(os.Stderr, "Usage: %s [options] DIRECTORY\n\n", os.Args[0])
	fmt.Fprintln(os.Stderr, "  DIRECTORY")
	fmt.Fprintln(os.Stderr, "    \tdirectory to find profile data")
	flag.PrintDefaults()
}

func main() {
	flag.Usage = Usage
	flag.Parse()

	remaining_args := flag.Args()

	if len(flag.Args()) != 1 {
		flag.Usage()
		os.Exit(2)
	}

	directory := remaining_args[0]
	maps_fn := path.Join(directory, "maps")
	map_, err := ParseMapX(maps_fn)
	check(err)
	unmapped_calls_fn := path.Join(directory, "unmapped-calls")

	acc := ReadFile(unmapped_calls_fn)

	pb := ProgressBar(
		len(acc),
		maps_fn)
	misses := 0
	index := NewIndex()
	for call := range acc {
		caller := map_.Translate(call.Caller)
		callee := map_.Translate(call.Callee)
		if caller == nil || callee == nil {
			misses++
			pb.Other = fmt.Sprintf(", misses: %d", misses)
		} else {
			index.New(call.Caller, caller.Pathname, caller.Offset)
			index.New(call.Callee, callee.Pathname, callee.Offset)
		}
		pb.Inc()
	}

	sort.Sort(ByPC(index.data))

	for pathname, offsets := range index.ObjectMap {
		log.Printf("%d addresses to be resolved in %v\n", len(offsets), pathname)
		var addresses []uint64
		for offset := range offsets {
			addresses = append(addresses, offset)
		}
		results := Addr2Line(path.Join("objects", path.Base(pathname)), addresses, *concurrency)
		for _, result := range results {
			address := result.Address
			offsets[address].Symbol = result.Symbol
			offsets[address].Source = result.Filename
			offsets[address].Line = result.Line
		}
	}

	Dump(os.Stdout, &acc, &index)
}
