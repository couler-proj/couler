package conversion

import (
	"testing"

	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	corev1 "k8s.io/api/core/v1"

	"github.com/alecthomas/assert"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
)

const manifest = `
        apiVersion: v1
        kind: Pod
        metadata:
          generateName: pi-job-
        spec:
          containers:
            - name: pi
              image: perl
              command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]`

var (
	containerStep = &pb.Step{
		Name:     "container-test-step",
		TmplName: "container-test",
		ContainerSpec: &pb.ContainerSpec{
			Image:   "docker/whalesay:latest",
			Command: []string{"cowsay", "hello world"},
		}}
	scriptStep = &pb.Step{
		Name:     "script-test-step",
		TmplName: "script-test",
		Script:   "print(3)",
		ContainerSpec: &pb.ContainerSpec{
			Image:   "python:alpine3.6",
			Command: []string{"python"},
		}}
	resourceStep = &pb.Step{
		Name:     "resource-test-step",
		TmplName: "resource-test",
		ResourceSpec: &pb.ResourceSpec{
			Manifest:          manifest,
			SuccessCondition:  "status.phase == Succeeded",
			FailureCondition:  "status.phase == Failed",
			SetOwnerReference: true,
			Action:            "create",
		},
	}
)

func TestArgoWorkflowConversionSequential(t *testing.T) {
	pbWf := &pb.Workflow{}
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
				{Name: containerStep.Name, Template: containerStep.TmplName},
			}},
			{Steps: []wfv1.WorkflowStep{
				{Name: scriptStep.Name, Template: scriptStep.TmplName},
			}},
			{Steps: []wfv1.WorkflowStep{
				{Name: resourceStep.Name, Template: resourceStep.TmplName},
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
		SetOwnerReference: resourceStep.ResourceSpec.SetOwnerReference,
		Action:            resourceStep.ResourceSpec.Action,
	}}, argoWf.Spec.Templates[3])
}

func TestArgoWorkflowConversionDAG(t *testing.T) {
	pbWf := &pb.Workflow{}
	scriptStep.Dependencies = []string{containerStep.TmplName}
	resourceStep.Dependencies = []string{containerStep.TmplName, scriptStep.TmplName}

	pbWf.Steps = []*pb.ConcurrentSteps{
		{Steps: []*pb.Step{containerStep}},
		{Steps: []*pb.Step{scriptStep}},
		{Steps: []*pb.Step{resourceStep}},
	}

	argoWf, err := ConvertToArgoWorkflow(pbWf, "hello-world-")
	assert.NoError(t, err)

	assert.Equal(t, 4, len(argoWf.Spec.Templates))
	assert.Equal(t,
		[]wfv1.DAGTask{
			{Name: containerStep.Name, Template: containerStep.TmplName},
			{Name: scriptStep.Name, Template: scriptStep.TmplName, Dependencies: []string{containerStep.TmplName}},
			{Name: resourceStep.Name, Template: resourceStep.TmplName, Dependencies: []string{containerStep.TmplName, scriptStep.TmplName}},
		}, argoWf.Spec.Templates[0].DAG.Tasks)
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
		SetOwnerReference: resourceStep.ResourceSpec.SetOwnerReference,
		Action:            resourceStep.ResourceSpec.Action,
	}}, argoWf.Spec.Templates[3])
}
