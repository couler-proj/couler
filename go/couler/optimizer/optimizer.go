package server

import (
	"fmt"

	pb "github.com/couler-proj/couler/go/couler/proto/couler_v1"
)

// Pass is the interface of the optimization pass
type Pass interface {
	Run(w *pb.Workflow) (*pb.Workflow, error)
}

// ComposedPass composed a sequence of optimization passes
type ComposedPass struct {
	passes []Pass
}

// Run all optimization passes
func (c *ComposedPass) Run(w *pb.Workflow) (*pb.Workflow, error) {
	for i, pass := range c.passes {
		w, e := pass.Run(w)
		if e != nil {
			return w, fmt.Errorf("optimization failed on %d-th pass", i)
		}
	}
	return w, nil
}

// Compose sequence optimization passes
func Compose(passes ...Pass) *ComposedPass {
	return &ComposedPass{passes: passes}
}
