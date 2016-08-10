package main

import (
	"fmt"
	"os"
)

type progress struct {
	total   int
	text    string
	current int
	last    int
	Other   string
}

func ProgressBar(total int, text string) progress {
	return progress{total: total, text: text}
}

func (p *progress) Inc() {
	p.current++
	next := p.current * 1000 / p.total
	if next != p.last {
		p.last = next
		p.Display()
		if p.total == p.current {
			fmt.Fprintln(os.Stderr, ", done.")
		}
	}
}

func (p *progress) Display() {
	fmt.Fprintf(os.Stderr, "\r%v: %v.%v%% (%v/%v)%v",
		p.text, p.last/10, p.last%10, p.current, p.total, p.Other)
}
