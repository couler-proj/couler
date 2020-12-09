package server_test

import (
	"testing"

	"github.com/alecthomas/assert"
	opt "github.com/couler-proj/couler/go/couler/optimization"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
)

type EndNodePass struct{}

func (p *EndNodePass) Run(w *pb.Workflow) (*pb.Workflow, error) {
	step := &pb.Step{Name: "endnode"}
	w.Steps = append(w.Steps, step)
	return w, nil
}

func TestComposePass(t *testing.T) {
	a := assert.New(t)
	w := &pb.Workflow{}
	w.Steps = []*pb.Step{&pb.Step{Name: "node1"}}

	// EndNodePass would add a node with name "endnode" at the tail
	opt := opt.Compose(&EndNodePass{})
	w, e := opt.Run(w)
	a.NoError(e)
	a.Equal(len(w.Steps), 2)
	a.Equal(w.Steps[1].Name, "endnode")
}
