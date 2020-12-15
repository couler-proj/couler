package conversion

import (
	"testing"

	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	corev1 "k8s.io/api/core/v1"

	"github.com/alecthomas/assert"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
)

func TestArgoWorkflowConversion(t *testing.T) {
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

	argoWf, err := ConvertToArgoWorkflow(pbWf, "hello-world-")
	assert.NoError(t, err)

	assert.Equal(t, 4, len(argoWf.Spec.Templates))
	assert.Equal(t,
		[]wfv1.ParallelSteps{
			{Steps: []wfv1.WorkflowStep{
				{Name: containerStep.TmplName, Template: containerStep.TmplName},
			}},
			{Steps: []wfv1.WorkflowStep{
				{Name: scriptStep.TmplName, Template: scriptStep.TmplName},
			}},
			{Steps: []wfv1.WorkflowStep{
				{Name: resourceStep.TmplName, Template: resourceStep.TmplName},
			}}}, argoWf.Spec.Templates[0].Steps)
	assert.Equal(t, wfv1.Template{Name: containerStep.TmplName, Container: &corev1.Container{
		Image:   containerStep.ContainerSpec.Image,
		Command: containerStep.ContainerSpec.Command,
	}}, argoWf.Spec.Templates[1])

	assert.Equal(t, wfv1.Template{Name: scriptStep.TmplName, Script: &wfv1.ScriptTemplate{
		Container: corev1.Container{
			Image:   scriptStep.ContainerSpec.Image,
			Command: scriptStep.ContainerSpec.Command,
		},
		Source: scriptStep.Script,
	}}, argoWf.Spec.Templates[2])
	assert.Equal(t, wfv1.Template{Name: resourceStep.TmplName, Resource: &wfv1.ResourceTemplate{
		Manifest:          resourceStep.ResourceSpec.Manifest,
		SuccessCondition:  resourceStep.ResourceSpec.SuccessCondition,
		FailureCondition:  resourceStep.ResourceSpec.FailureCondition,
		SetOwnerReference: true,
		Action:            "create",
	}}, argoWf.Spec.Templates[3])
}
