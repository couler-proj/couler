package optimization

import (
	"fmt"

	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
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
	var err error
	for i, pass := range c.passes {
		w, err = pass.Run(w)
		if err != nil {
			return nil, fmt.Errorf("optimization failed on %d-th pass", i)
		}
	}
	return w, nil
}

// Compose sequence optimization passes
func Compose(passes ...Pass) *ComposedPass {
	return &ComposedPass{passes: passes}
}
