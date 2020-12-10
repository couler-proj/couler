package conversion

import (
	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func convertToArgoWorkflow(workflowPb *pb.Workflow, namePrefix string) (wfv1.Workflow, error) {
	templates := []wfv1.Template{{}}
	// TODO: Handle DAG tasks.
	for _, step := range workflowPb.GetSteps() {
		template := wfv1.Template{Name: step.TmplName}
		// TODO: Check mutual exclusivity of different specs.
		if step.GetContainerSpec() != nil || step.GetScript() != "" {
			containerSpec := step.GetContainerSpec()
			container := &corev1.Container{
				Image:   containerSpec.GetImage(),
				Command: containerSpec.GetCommand(),
				// TODO: Convert type map[string]*any.Any) to type []EnvVar that's supported by Argo.
				//Env: containerSpec.GetEnv(),
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
				// TODO: Check whether these hard-coded fields need to be exposed.
				SetOwnerReference: true,
				Action:            "create",
				Manifest:          resourceSpec.GetManifest(),
				SuccessCondition:  resourceSpec.GetSuccessCondition(),
				FailureCondition:  resourceSpec.GetSuccessCondition(),
			}
		}
		templates = append(templates, template)
	}
	argoWorkflow := wfv1.Workflow{
		ObjectMeta: metav1.ObjectMeta{
			GenerateName: namePrefix,
		},
		Spec: wfv1.WorkflowSpec{
			Entrypoint: workflowPb.GetSteps()[0].TmplName, // TODO: Check whether we can rely on this order.
			Templates:  templates,
		},
	}
	// TODO: Handle workflow schema validation and propagate any errors.
	return argoWorkflow, nil
}
