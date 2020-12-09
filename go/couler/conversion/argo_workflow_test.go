package conversion

import (
	"testing"

	"github.com/alecthomas/assert"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
)

func TestArgoWorkflowConversion(t *testing.T) {
	w := &pb.Workflow{}
	w.Steps = []*pb.Step{&pb.Step{Name: "node1"}}

	assert.Equal(t, len(w.Steps), 2)
	out, err := ConvertToArgoWorkflowYAML(w)
	assert.NoError(t, err)
	assert.Equal(t, w.String(), out)
}
