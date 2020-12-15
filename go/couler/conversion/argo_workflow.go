package conversion

import (
	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const sequentialStepsTemplateSuffix = "main-template"

// ConvertToArgoWorkflow converts a workflow from protobuf to an Argo Workflow
func ConvertToArgoWorkflow(workflowPb *pb.Workflow, namePrefix string) (wfv1.Workflow, error) {
	templates := []wfv1.Template{{Name: namePrefix + sequentialStepsTemplateSuffix}}
	// TODO: Handle DAG tasks.
	for _, step := range workflowPb.GetSteps() {
		seqStep := step.Steps[0]
		templates[0].Steps = append(templates[0].Steps,
			wfv1.ParallelSteps{
				Steps: []wfv1.WorkflowStep{{Name: seqStep.TmplName, Template: seqStep.TmplName}}})
		template := wfv1.Template{Name: seqStep.TmplName}
		// TODO: Check mutual exclusivity of different specs.
		if seqStep.GetContainerSpec() != nil || seqStep.GetScript() != "" {
			containerSpec := seqStep.GetContainerSpec()
			container := &corev1.Container{
				Image:   containerSpec.GetImage(),
				Command: containerSpec.GetCommand(),
				// TODO: Convert type map[string]*any.Any) to type []EnvVar that's supported by Argo.
				//Env: containerSpec.GetEnv(),
			}
			if script := seqStep.GetScript(); script != "" {
				template.Script = &wfv1.ScriptTemplate{
					Container: *container,
					Source:    script,
				}
			} else {
				template.Container = container
			}
		} else if resourceSpec := seqStep.GetResourceSpec(); resourceSpec != nil {
			template.Resource = &wfv1.ResourceTemplate{
				// TODO: Check whether these hard-coded fields need to be exposed.
				SetOwnerReference: true,
				Action:            "create",
				Manifest:          resourceSpec.GetManifest(),
				SuccessCondition:  resourceSpec.GetSuccessCondition(),
				FailureCondition:  resourceSpec.GetFailureCondition(),
			}
		}
		templates = append(templates, template)
	}
	argoWorkflow := wfv1.Workflow{
		ObjectMeta: metav1.ObjectMeta{
			GenerateName: namePrefix,
		},
		Spec: wfv1.WorkflowSpec{
			// TODO: Check whether we can rely on this order. We need to use
			// 	the step that has the smallest id here instead.
			Entrypoint: workflowPb.GetSteps()[0].Steps[0].TmplName,
			Templates:  templates,
		},
	}
	// TODO: Handle workflow schema validation and propagate any errors.
	return argoWorkflow, nil
}
