package submitter

import (
	"fmt"
	"github.com/alecthomas/assert"
	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	"github.com/couler-proj/couler/go/couler/conversion"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
	"os"
	"os/user"
	"path/filepath"
	"testing"
)

func TestArgoWorkflowSubmitter(t *testing.T) {
	toTest := os.Getenv("E2E_TEST")
	if toTest == "" || toTest == "false" {
		t.Skip("Skipping end-to-end tests")
	}
	pbWf := &pb.Workflow{}
	containerStep := &pb.Step{
		TmplName: "container-test", ContainerSpec: &pb.ContainerSpec{
			Image:   "docker/whalesay:latest",
			Command: []string{"cowsay", "hello world"},
		}}
	scriptStep := &pb.Step{
		TmplName: "script-test", Script: "print(3)", ContainerSpec: &pb.ContainerSpec{
			Image:   "docker/whalesay:latest",
			Command: []string{"python"},
		}}
	manifest := `
        apiVersion: batch/v1
        kind: Job
        metadata:
          generateName: pi-job-
        spec:
          template:
            metadata:
              name: pi
            spec:
              containers:
              - name: pi
                image: perl
                command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]
              restartPolicy: Never
          backoffLimit: 4`
	resourceStep := &pb.Step{
		TmplName: "resource-test", ResourceSpec: &pb.ResourceSpec{
			Manifest:         manifest,
			SuccessCondition: "status.succeeded > 0",
			FailureCondition: "status.failed > 3",
		},
	}
	pbWf.Steps = []*pb.ConcurrentSteps{
		{Steps: []*pb.Step{containerStep}},
		{Steps: []*pb.Step{scriptStep}},
		{Steps: []*pb.Step{resourceStep}},
	}

	argoWf, err := conversion.ConvertToArgoWorkflow(pbWf, "hello-world-")
	assert.NoError(t, err)

	// get current user to determine home directory
	usr, err := user.Current()
	assert.NoError(t, err)

	submitter := ArgoWorkflowSubmitter{
		namespace:      "argo",
		kubeConfigPath: filepath.Join(usr.HomeDir, ".kube", "config"),
	}
	finishedArgoWf, err := submitter.Submit(argoWf, true)
	if err != nil && finishedArgoWf != nil {
		fmt.Printf("Workflow %s failed due to %s. \nStatuses of each workflow nodes:\n", finishedArgoWf.Name, err)
		for _, node := range finishedArgoWf.Status.Nodes {
			fmt.Printf("Node %s %s. Message: %s\n", node.Name, node.Phase, node.Message)
		}
	}
	assert.NotNil(t, finishedArgoWf)
	assert.NoError(t, err)
	assert.Equal(t, wfv1.NodeSucceeded, finishedArgoWf.Status.Phase)
	assert.False(t, finishedArgoWf.Status.FinishedAt.IsZero())

	unfinishedArgoWf, err := conversion.ConvertToArgoWorkflow(pbWf, "unfinished-hello-world-")
	assert.NoError(t, err)
	submittedUnfinishedArgoWf, err := submitter.Submit(unfinishedArgoWf, false)
	assert.NoError(t, err)
	assert.True(t, submittedUnfinishedArgoWf.Status.FinishedAt.IsZero())
}
