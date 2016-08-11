package main

import (
	"bufio"
	"bytes"
	"errors"
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"

	"golang.org/x/net/context"
	"golang.org/x/sync/errgroup"
)

type AddrInfo struct {
	Address  uint64
	Symbol   string
	Filename string
	Line     string
}

var command = flag.String("addr2line", "eu-addr2line", "specify the addr2line command")

func addr2line_worker(ctx context.Context, filename string, addresses []uint64, ch chan<- AddrInfo) error {
	cmd := exec.Command(*command, "-f", "-e", filename)

	stdin := new(bytes.Buffer)
	cmd.Stdin = stdin

	for _, address := range addresses {
		fmt.Fprintf(stdin, "%x\n", address)
	}

	stdout_pipe, err := cmd.StdoutPipe()
	if err != nil {
		return err
	}

	stdout := bufio.NewReader(stdout_pipe)

	err = cmd.Start()
	defer cmd.Process.Kill()

	cmd.Stderr = os.Stderr

	if err != nil {
		return err
	}

	for _, address := range addresses {
		select {
		case <-ctx.Done():
			cmd.Process.Kill()
		default:
			symbol, err := stdout.ReadString('\n')
			if err != nil {
				return err
			}
			location, err := stdout.ReadString('\n')
			if err != nil {
				return err
			}
			location = strings.TrimSpace(location)
			location_arr := strings.SplitN(location, ":", 2)
			if len(location_arr) != 2 {
				return errors.New(fmt.Sprintf("unexpected addr2line output %q", location))
			}
			ch <- AddrInfo{
				address,
				strings.TrimSpace(symbol),
				location_arr[0],
				location_arr[1],
			}
		}
	}
	return nil
}

func Addr2Line(filename string, addresses []uint64, workers int) []AddrInfo {
	_, err := os.Stat(filename)
	if err != nil {
		if os.IsNotExist(err) {
			log.Printf("%s does not exist, skipping", filename)
			return nil
		}
		panic(err)
	}

	if workers > len(addresses) {
		workers = len(addresses)
	}

	group, ctx := errgroup.WithContext(context.Background())

	returning := make([]AddrInfo, len(addresses))
	ch := make(chan AddrInfo)

	pb := ProgressBar(len(addresses), "addr2line")

	group.Go(func() error {
		for i := range addresses {
			select {
			case <-ctx.Done():
				return nil
			case returning[i] = <-ch:
				pb.Inc()
			}
		}
		return nil
	})

	div := len(addresses) / workers
	mod := len(addresses) % workers
	start := 0
	for i := 0; i < workers; i++ {
		stop := start + div
		if i < mod {
			stop++
		}
		addresses := addresses[start:stop]
		group.Go(func() error {
			return addr2line_worker(ctx, filename, addresses, ch)
		})
		start = stop
	}

	if err := group.Wait(); err == nil {
		return returning
	} else {
		panic(err)
	}
}
