package conversion

import (
	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const entrypointTemplateSuffix = "main-template"

// ConvertToArgoWorkflow converts a workflow from protobuf to an Argo Workflow
func ConvertToArgoWorkflow(workflowPb *pb.Workflow, namePrefix string) (wfv1.Workflow, error) {
	// Check whether the workflow is DAG.
	dagMode := false
	for _, step := range workflowPb.GetSteps() {
		if step.Steps[0].Dependencies != nil {
			dagMode = true
			break
		}
	}
	templates := []wfv1.Template{{Name: namePrefix + entrypointTemplateSuffix}}
	// Convert steps to DAG tasks.
	if dagMode {
		templates[0].DAG = &wfv1.DAGTemplate{
			Tasks: []wfv1.DAGTask{},
		}
		for _, step := range workflowPb.GetSteps() {
			seqStep := step.Steps[0]
			templates[0].DAG.Tasks = append(templates[0].DAG.Tasks,
				wfv1.DAGTask{
					Name:         seqStep.GetName(),
					Template:     seqStep.GetTmplName(),
					Dependencies: seqStep.GetDependencies(),
				})
			templates = append(templates, createStepTemplate(seqStep))
		}
	} else {
		// Convert steps to sequential/parallel steps.
		for _, step := range workflowPb.GetSteps() {
			seqStep := step.Steps[0]
			templates[0].Steps = append(templates[0].Steps,
				wfv1.ParallelSteps{
					Steps: []wfv1.WorkflowStep{{Name: seqStep.GetName(), Template: seqStep.GetTmplName()}}})

			templates = append(templates, createStepTemplate(seqStep))
		}
	}
	argoWorkflow := wfv1.Workflow{
		ObjectMeta: metav1.ObjectMeta{
			GenerateName: namePrefix,
		},
		Spec: wfv1.WorkflowSpec{
			Entrypoint: namePrefix + entrypointTemplateSuffix,
			Templates:  templates,
		},
	}
	// TODO: Handle workflow schema validation and propagate any errors.
	return argoWorkflow, nil
}

func createStepTemplate(step *pb.Step) wfv1.Template {
	template := wfv1.Template{Name: step.TmplName}
	// TODO: Check mutual exclusivity of different specs.
	if step.GetContainerSpec() != nil || step.GetScript() != "" {
		containerSpec := step.GetContainerSpec()
		var env []corev1.EnvVar
		for k, v := range containerSpec.GetEnv() {
			env = append(env, corev1.EnvVar{Name: k, Value: v.String()})
		}
		container := &corev1.Container{
			Image:   containerSpec.GetImage(),
			Command: containerSpec.GetCommand(),
			Env:     env,
		}
		if script := step.GetScript(); script != "" {
			template.Script = &wfv1.ScriptTemplate{
				Container: *container,
				Source:    script,
			}
		} else {
			template.Container = container
		}
	} else if resourceSpec := step.GetResourceSpec(); resourceSpec != nil {
		template.Resource = &wfv1.ResourceTemplate{
			SetOwnerReference: resourceSpec.GetSetOwnerReference(),
			Action:            resourceSpec.GetAction(),
			Manifest:          resourceSpec.GetManifest(),
			SuccessCondition:  resourceSpec.GetSuccessCondition(),
			FailureCondition:  resourceSpec.GetFailureCondition(),
		}
	}
	return template
}
