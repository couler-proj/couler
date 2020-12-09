package conversion

import (
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
)

func convertToArgoWorkflowYAML(w *pb.Workflow) (string, error) {
	return w.String(), nil
}
