package main

import (
	"flag"
	"fmt"
	"github.com/couler-proj/couler/go/couler/conversion"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
	"github.com/couler-proj/couler/go/couler/submitter"
	"github.com/golang/protobuf/proto"
	"io/ioutil"
	"log"
	"os/user"
	"path/filepath"
)

func main() {
	filePath := flag.String("proto-path", "", "Path to the workflow protobuf")
	namespace := flag.String("namespace", "default", "The namespace name")
	namePrefix := flag.String("name-prefix", "", "The prefix for the workflow name")
	flag.Parse()

	// Testing submitting probuf written from Python
	in, err := ioutil.ReadFile(*filePath)
	if err != nil {
		log.Fatalln("Failed to read file:", err)
	}
	pbWf := &pb.Workflow{}
	err = proto.Unmarshal(in, pbWf)
	if err != nil {
		log.Fatalln("Failed to unmarshal workflow pb:", err)
	}
	argoWf, err := conversion.ConvertToArgoWorkflow(pbWf, *namePrefix)
	if err != nil {
		log.Fatalln("Failed to convert to Argo Workflow:", err)
	}

	// get current user to determine home directory
	usr, err := user.Current()
	if err != nil {
		log.Fatalln("Failed to get the current user:", err)
	}
	sub := submitter.ArgoWorkflowSubmitter{
		Namespace: *namespace,
		// TODO: Support in-cluster configuration
		KubeConfigPath: filepath.Join(usr.HomeDir, ".kube", "config"),
	}
	finishedArgoWf, err := sub.Submit(argoWf, true)
	if err != nil && finishedArgoWf != nil {
		fmt.Printf("Workflow read from protobuf %s failed due to %s. \nStatuses of each workflow nodes:\n", finishedArgoWf.Name, err)
		for _, node := range finishedArgoWf.Status.Nodes {
			fmt.Printf("Node %s %s. Message: %s\n", node.Name, node.Phase, node.Message)
		}
	}
}
