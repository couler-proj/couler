package optimization

import (
	"testing"

	"github.com/alecthomas/assert"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
)

type EndNodePass struct{}

func (p *EndNodePass) Run(w *pb.Workflow) (*pb.Workflow, error) {
	stepList := &pb.ConcurrentSteps{
		Steps: []*pb.Step{{Name: "endnode"}},
	}
	w.Steps = append(w.Steps, stepList)
	return w, nil
}

func TestComposePass(t *testing.T) {
	a := assert.New(t)
	w := &pb.Workflow{}
	w.Steps = []*pb.ConcurrentSteps{
		{
			Steps: []*pb.Step{{Name: "node1"}},
		},
	}

	// EndNodePass would add a node with name "endnode" at the tail
	opt := Compose(&EndNodePass{})
	w, e := opt.Run(w)
	a.NoError(e)
	a.Equal(len(w.Steps), 2)
	a.Equal(w.Steps[1].Steps[0].Name, "endnode")
}
