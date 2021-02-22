package main

import (
	"C"
	"fmt"
	"github.com/couler-proj/couler/go/couler/conversion"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
	"github.com/couler-proj/couler/go/couler/submitter"
	"github.com/golang/protobuf/proto"
	"io/ioutil"
	"os/user"
	"path/filepath"
)

// Submit is the main function that submits a workflow protobuf.
//export Submit
func Submit(cProtoPath, cNamespace, cNamePrefix *C.char) *C.char {
	protoPath := C.GoString(cProtoPath)
	namespace := C.GoString(cNamespace)
	namePrefix := C.GoString(cNamePrefix)

	in, err := ioutil.ReadFile(protoPath)
	if err != nil {
		return wrapError(fmt.Errorf("failed to read workflow protobuf file: %w", err))
	}
	pbWf := &pb.Workflow{}
	err = proto.Unmarshal(in, pbWf)
	if err != nil {
		return wrapError(fmt.Errorf("failed to unmarshal workflow pb: %w", err))
	}
	argoWf, err := conversion.ConvertToArgoWorkflow(pbWf, namePrefix)
	if err != nil {
		return wrapError(fmt.Errorf("failed to convert to Argo Workflow: %w", err))
	}

	// get current user to determine home directory
	usr, err := user.Current()
	if err != nil {
		return wrapError(fmt.Errorf("failed to get the current user: %w", err))
	}
	sub := submitter.New(namespace, filepath.Join(usr.HomeDir, ".kube", "config"))
	submittedArgoWf, err := sub.Submit(argoWf, true)
	if err != nil && submittedArgoWf != nil {
		var errMsg string
		errMsg += fmt.Sprintf("Workflow read from protobuf %s failed due to: %v. \nStatuses of each workflow nodes:\n", submittedArgoWf.Name, err)
		for _, node := range submittedArgoWf.Status.Nodes {
			errMsg += fmt.Sprintf("Node %s %s. Message: %s\n", node.Name, node.Phase, node.Message)
		}
		return C.CString(errMsg)
	}
	return C.CString("Success")
}

func wrapError(err error) *C.char {
	return C.CString(err.Error())
}

func main() {}
