package main

import (
	"bufio"
	"encoding/binary"
	"io"
	"os"
)

type UnmappedCall struct {
	Caller uint64 `json:"caller"`
	Callee uint64 `json:"callee"`
}

func ReadFile(filename string) map[UnmappedCall]uint64 {
	calls := make(map[UnmappedCall]uint64)

	file, err := os.Open(filename)
	if err != nil {
		panic(err)
	}
	defer file.Close()
	reader := bufio.NewReader(file)
	stat, err := file.Stat()
	if err != nil {
		panic(err)
	}
	var call32 [2]uint32
	pb := ProgressBar(int(stat.Size()/8), filename)
	for {
		err := binary.Read(reader, binary.LittleEndian, &call32)
		if err != nil {
			if err == io.EOF {
				break
			}
			panic(err)
		}
		calls[UnmappedCall{uint64(call32[0]), uint64(call32[1])}]++
		pb.Inc()
	}
	return calls
}
