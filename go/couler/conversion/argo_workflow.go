package conversion

import (
	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const entryPointTemplateSuffix = "main-template"

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
	entryPointName := namePrefix + entryPointTemplateSuffix
	var templates []wfv1.Template
	if dagMode {
		// Convert steps to DAG tasks.
		templates = createDAGTasks(workflowPb, entryPointName)
	} else {
		// Convert steps to sequential/parallel steps.
		templates = createSeqOrParallelSteps(workflowPb, entryPointName)
	}
	argoWorkflow := wfv1.Workflow{
		ObjectMeta: metav1.ObjectMeta{
			GenerateName: namePrefix,
		},
		Spec: wfv1.WorkflowSpec{
			Entrypoint: entryPointName,
			Templates:  templates,
		},
	}
	// TODO: Handle workflow schema validation and propagate any errors.
	return argoWorkflow, nil
}

func getArgs(step *pb.Step) wfv1.Arguments {
	var args wfv1.Arguments
	for _, arg := range step.GetArgs() {
		switch stepIOType := arg.GetStepIo().(type) {
		case *pb.StepIO_Parameter:
			args.Parameters = append(args.Parameters, wfv1.Parameter{
				Name:             stepIOType.Parameter.GetName(),
				Value:			  &stepIOType.Parameter.Value,
				// TODO: This is not in proto def yet.
				//GlobalName: 		stepIOType.Parameter.GlobalName,
			})
		case *pb.StepIO_Artifact:
			args.Artifacts = append(args.Artifacts, wfv1.Artifact{
				Name:             stepIOType.Artifact.GetName(),
				Path:             stepIOType.Artifact.GetLocalPath(),
				From:             stepIOType.Artifact.GetValue(),
				// TODO: This is not used internally yet. Implement this when needed.
				//ArtifactLocation: wfv1.ArtifactLocation{},
				GlobalName:       stepIOType.Artifact.GetGlobalName(),
			})
		//case *pb.StepIO_Stdout:
		//case nil:
		default:
			//return fmt.Errorf("Profile.Avatar has unexpected type %T", x)
		}
	}
	return args
}

func getInputsAndOutputs(step *pb.Step) (wfv1.Inputs, wfv1.Outputs) {
	
}

func createDAGTasks(workflowPb *pb.Workflow, entryPointName string) []wfv1.Template {
	templates := []wfv1.Template{{Name: entryPointName}}
	// Convert steps to DAG tasks.
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
				Arguments: getArgs(seqStep),
			})
		templates = append(templates, createSingleStepTemplate(seqStep))
	}
	return templates
}

func createSeqOrParallelSteps(workflowPb *pb.Workflow, entryPointName string) []wfv1.Template {
	templates := []wfv1.Template{{Name: entryPointName}}
	for _, step := range workflowPb.GetSteps() {
		seqStep := step.Steps[0]
		templates[0].Steps = append(templates[0].Steps,
			wfv1.ParallelSteps{
				Steps: []wfv1.WorkflowStep{
					{Name: seqStep.GetName(), Template: seqStep.GetTmplName(), Arguments: getArgs(seqStep)}}})

		templates = append(templates, createSingleStepTemplate(seqStep))
	}
	return templates
}

func createSingleStepTemplate(step *pb.Step) wfv1.Template {
	template := wfv1.Template{
		Name: step.TmplName,
		Inputs: }
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
