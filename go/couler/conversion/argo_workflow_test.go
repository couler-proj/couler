package conversion

import (
	"testing"

	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	corev1 "k8s.io/api/core/v1"
	resourcev1 "k8s.io/apimachinery/pkg/api/resource"

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
			Image:     "python:alpine3.6",
			Command:   []string{"python"},
			Resources: map[string]string{"cpu": "2", "memory": "1Gi"},
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

	resourceList := corev1.ResourceList{}
	for k, v := range scriptStep.ContainerSpec.GetResources() {
		resourceList[corev1.ResourceName(k)] = resourcev1.MustParse(v)
	}
	resourceReq := corev1.ResourceRequirements{
		Requests: resourceList,
		Limits:   resourceList,
	}

	argoWf, err := ConvertToArgoWorkflow(pbWf, "hello-world-")
	assert.NoError(t, err)

	assert.Equal(t, argoWf.ObjectMeta.GenerateName, "hello-world-")

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
			Image:     scriptStep.ContainerSpec.Image,
			Command:   scriptStep.ContainerSpec.Command,
			Resources: resourceReq,
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

func TestArgoWorkflowConversionSequentialWithIO(t *testing.T) {
	paramValue := "hello world"
	containerStepWithIO := &pb.Step{
		Name:     "container-test-step",
		TmplName: "container-test",
		ContainerSpec: &pb.ContainerSpec{
			Image:   "docker/whalesay:latest",
			Command: []string{"cowsay"},
		},
		Args: []*pb.StepIO{{
			Name:   "message",
			Source: 0,
			StepIo: &pb.StepIO_Parameter{Parameter: &pb.Parameter{
				Name:  "message",
				Value: paramValue,
			}},
		}},
	}
	pbWf := &pb.Workflow{Templates: map[string]*pb.StepTemplate{
		containerStep.TmplName: {
			Name: containerStepWithIO.TmplName,
			Inputs: []*pb.StepIO{{
				Name:   "message",
				Source: 0,
				StepIo: &pb.StepIO_Parameter{Parameter: &pb.Parameter{
					Name:  "message",
					Value: paramValue,
				}},
			}},
		},
		scriptStep.TmplName:   {Name: scriptStep.TmplName},
		resourceStep.TmplName: {Name: resourceStep.TmplName},
	}}
	pbWf.Steps = []*pb.ConcurrentSteps{
		{Steps: []*pb.Step{containerStepWithIO}},
		{Steps: []*pb.Step{scriptStep}},
		{Steps: []*pb.Step{resourceStep}},
	}

	argoWf, err := ConvertToArgoWorkflow(pbWf, "hello-world-")
	assert.NoError(t, err)

	assert.Equal(t, 4, len(argoWf.Spec.Templates))
	assert.Equal(t,
		[]wfv1.ParallelSteps{
			{Steps: []wfv1.WorkflowStep{
				{Name: containerStepWithIO.Name, Template: containerStepWithIO.TmplName, Arguments: wfv1.Arguments{
					Parameters: []wfv1.Parameter{{
						Name:  "message",
						Value: &paramValue,
					}},
				},
				}}},
			{Steps: []wfv1.WorkflowStep{
				{Name: scriptStep.Name, Template: scriptStep.TmplName},
			}},
			{Steps: []wfv1.WorkflowStep{
				{Name: resourceStep.Name, Template: resourceStep.TmplName},
			}}}, argoWf.Spec.Templates[0].Steps)
	assert.Equal(t, wfv1.Template{
		Name: containerStepWithIO.TmplName,
		Container: &corev1.Container{Image: containerStepWithIO.ContainerSpec.Image,
			Command: containerStepWithIO.ContainerSpec.Command},
		Inputs: wfv1.Inputs{
			Parameters: []wfv1.Parameter{{
				Name:  "message",
				Value: &paramValue,
			}},
		},
	}, argoWf.Spec.Templates[1])
}

func TestArgoWorkflowConversionSequentialWithExitHandler(t *testing.T) {
	pbWf := &pb.Workflow{}
	pbWf.Steps = []*pb.ConcurrentSteps{
		{Steps: []*pb.Step{containerStep}},
		{Steps: []*pb.Step{scriptStep}},
		{Steps: []*pb.Step{resourceStep}},
	}
	resourceList := corev1.ResourceList{}
	for k, v := range scriptStep.ContainerSpec.GetResources() {
		resourceList[corev1.ResourceName(k)] = resourcev1.MustParse(v)
	}
	resourceReq := corev1.ResourceRequirements{
		Requests: resourceList,
		Limits:   resourceList,
	}

	exitHandlerStep := &pb.Step{
		Name:     "exit-handler-step",
		TmplName: "exit-handler-step-template",
		ContainerSpec: &pb.ContainerSpec{
			Image:   "docker/whalesay:latest",
			Command: []string{"cowsay", "exiting"},
		},
		When: "{{workflow.status}} == Failed",
	}
	pbWf.ExitHandlerSteps = append(pbWf.ExitHandlerSteps, exitHandlerStep)

	argoWf, err := ConvertToArgoWorkflow(pbWf, "hello-world-")
	assert.NoError(t, err)

	assert.Equal(t, 6, len(argoWf.Spec.Templates))
	// Check the steps in entry-point template,
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

	// Check the templates for individual steps.
	assert.Equal(t, wfv1.Template{Name: containerStep.TmplName, Container: &corev1.Container{
		Image:   containerStep.ContainerSpec.Image,
		Command: containerStep.ContainerSpec.Command,
	}}, argoWf.Spec.Templates[1])
	assert.Equal(t, wfv1.Template{Name: scriptStep.TmplName, Script: &wfv1.ScriptTemplate{
		Container: corev1.Container{
			Image:     scriptStep.ContainerSpec.Image,
			Command:   scriptStep.ContainerSpec.Command,
			Resources: resourceReq,
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
	// Check the templates for exit handler steps.
	assert.Equal(t, wfv1.Template{Name: exitHandlerStep.TmplName, Container: &corev1.Container{
		Image:   exitHandlerStep.ContainerSpec.Image,
		Command: exitHandlerStep.ContainerSpec.Command,
	}}, argoWf.Spec.Templates[4])
	assert.Equal(t, []wfv1.ParallelSteps{{Steps: []wfv1.WorkflowStep{
		{Name: exitHandlerStep.Name, Template: exitHandlerStep.TmplName, When: exitHandlerStep.When},
	}}}, argoWf.Spec.Templates[5].Steps)

	// Check the on-exit template name.
	assert.Equal(t, "hello-world-exit-handler-steps", argoWf.Spec.OnExit)
}

func TestArgoWorkflowConversionDAG(t *testing.T) {
	pbWf := &pb.Workflow{Name: "wf-dag"}
	scriptStep.Dependencies = []string{containerStep.TmplName}
	resourceStep.Dependencies = []string{containerStep.TmplName, scriptStep.TmplName}

	pbWf.Steps = []*pb.ConcurrentSteps{
		{Steps: []*pb.Step{containerStep}},
		{Steps: []*pb.Step{scriptStep}},
		{Steps: []*pb.Step{resourceStep}},
	}

	resourceList := corev1.ResourceList{}
	for k, v := range scriptStep.ContainerSpec.GetResources() {
		resourceList[corev1.ResourceName(k)] = resourcev1.MustParse(v)
	}
	resourceReq := corev1.ResourceRequirements{
		Requests: resourceList,
		Limits:   resourceList,
	}

	argoWf, err := ConvertToArgoWorkflow(pbWf, "")
	assert.NoError(t, err)

	assert.Equal(t, argoWf.ObjectMeta.Name, pbWf.Name)

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
			Image:     scriptStep.ContainerSpec.Image,
			Command:   scriptStep.ContainerSpec.Command,
			Resources: resourceReq,
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
