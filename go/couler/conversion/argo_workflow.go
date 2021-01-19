package conversion

import (
	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
	corev1 "k8s.io/api/core/v1"
	resourcev1 "k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const entryPointTemplateSuffix = "main-template"
const exitHandlerTemplateSuffix = "exit-handler-steps"

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
	var objectMeta metav1.ObjectMeta
	if name := workflowPb.GetName(); name != "" && namePrefix == "" {
		objectMeta = metav1.ObjectMeta{
			Name: name,
		}
	} else {
		objectMeta = metav1.ObjectMeta{
			GenerateName: namePrefix,
		}
	}
	argoWorkflow := wfv1.Workflow{
		ObjectMeta: objectMeta,
		Spec: wfv1.WorkflowSpec{
			Entrypoint: entryPointName,
			Templates:  templates,
		},
	}
	if workflowPb.GetExitHandlerSteps() != nil {
		exitHandlerTemplateName := namePrefix + exitHandlerTemplateSuffix
		argoWorkflow.Spec.Templates = createExitHandlerSteps(workflowPb, argoWorkflow.Spec.Templates, exitHandlerTemplateName)
		argoWorkflow.Spec.OnExit = exitHandlerTemplateName
	}
	// TODO: Handle workflow schema validation and propagate any errors.
	return argoWorkflow, nil
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
				Arguments:    getEntryPointTemplateArgs(seqStep),
				When:         seqStep.GetWhen(),
			})
		templates = append(templates, createSingleStepTemplate(seqStep, workflowPb))
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
					{Name: seqStep.GetName(), Template: seqStep.GetTmplName(),
						Arguments: getEntryPointTemplateArgs(seqStep), When: seqStep.GetWhen()}}})

		templates = append(templates, createSingleStepTemplate(seqStep, workflowPb))
	}
	return templates
}

func createExitHandlerSteps(workflowPb *pb.Workflow, templates []wfv1.Template, exitHandlerTemplateName string) []wfv1.Template {
	template := wfv1.Template{Name: exitHandlerTemplateName}
	for _, step := range workflowPb.GetExitHandlerSteps() {
		template.Steps = append(template.Steps,
			wfv1.ParallelSteps{
				Steps: []wfv1.WorkflowStep{
					{Name: step.GetName(), Template: step.GetTmplName(), When: step.GetWhen()}}})
		templates = append(templates, createSingleStepTemplate(step, workflowPb))
	}
	templates = append(templates, template)
	return templates
}

func createSingleStepTemplate(step *pb.Step, workflowPb *pb.Workflow) wfv1.Template {
	inputs, outputs := getInputsAndOutputsFromTemplate(workflowPb.GetTemplates()[step.TmplName])
	template := wfv1.Template{
		Name:    step.TmplName,
		Inputs:  inputs,
		Outputs: outputs}
	// TODO: Check mutual exclusivity of different specs.
	if step.GetContainerSpec() != nil || step.GetScript() != "" {
		containerSpec := step.GetContainerSpec()
		var env []corev1.EnvVar
		for k, v := range containerSpec.GetEnv() {
			env = append(env, corev1.EnvVar{Name: k, Value: v})
		}
		container := &corev1.Container{
			Image:   containerSpec.GetImage(),
			Command: containerSpec.GetCommand(),
			Env:     env,
		}
		if len(containerSpec.GetResources()) > 0 {
			resourceList := corev1.ResourceList{}
			for k, v := range containerSpec.GetResources() {
				resourceList[corev1.ResourceName(k)] = resourcev1.MustParse(v)
			}
			resourceReq := corev1.ResourceRequirements{
				// NOTE: request for hard resource limit.
				Requests: resourceList,
				Limits:   resourceList,
			}
			container.Resources = resourceReq
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

func getEntryPointTemplateArgs(step *pb.Step) wfv1.Arguments {
	var args wfv1.Arguments
	for _, arg := range step.GetArgs() {
		switch stepIOType := arg.GetStepIo().(type) {
		case *pb.StepIO_Parameter:
			args.Parameters = append(args.Parameters, wfv1.Parameter{
				Name:  stepIOType.Parameter.GetName(),
				Value: &stepIOType.Parameter.Value,
			})
		case *pb.StepIO_Artifact:
			args.Artifacts = append(args.Artifacts, wfv1.Artifact{
				Name: stepIOType.Artifact.GetName(),
				From: stepIOType.Artifact.GetValue(),
			})
		}
	}
	return args
}

func getInputsAndOutputsFromTemplate(template *pb.StepTemplate) (wfv1.Inputs, wfv1.Outputs) {
	var inputs wfv1.Inputs
	for _, input := range template.GetInputs() {
		switch stepIOType := input.GetStepIo().(type) {
		case *pb.StepIO_Parameter:
			inputs.Parameters = append(inputs.Parameters, wfv1.Parameter{
				Name:       stepIOType.Parameter.GetName(),
				Value:      &stepIOType.Parameter.Value,
				GlobalName: stepIOType.Parameter.GlobalName,
			})
		case *pb.StepIO_Artifact:
			artifactLocation := wfv1.ArtifactLocation{}

			if stepIOType.Artifact.Type == "OSS" {
				artifactLocation = wfv1.ArtifactLocation{OSS: &wfv1.OSSArtifact{
					OSSBucket: wfv1.OSSBucket{
						Endpoint: stepIOType.Artifact.Endpoint,
						Bucket:   stepIOType.Artifact.Bucket,
						AccessKeySecret: corev1.SecretKeySelector{LocalObjectReference: corev1.LocalObjectReference{
							Name: stepIOType.Artifact.AccessKey.Name}, Key: stepIOType.Artifact.AccessKey.Key},
						SecretKeySecret: corev1.SecretKeySelector{LocalObjectReference: corev1.LocalObjectReference{
							Name: stepIOType.Artifact.SecretKey.Name}, Key: stepIOType.Artifact.SecretKey.Key},
					},
					Key: stepIOType.Artifact.RemotePath,
				}}
			} else if stepIOType.Artifact.Type == "S3" {
				artifactLocation = wfv1.ArtifactLocation{S3: &wfv1.S3Artifact{
					S3Bucket: wfv1.S3Bucket{
						Endpoint: stepIOType.Artifact.Endpoint,
						Bucket:   stepIOType.Artifact.Bucket,
						AccessKeySecret: corev1.SecretKeySelector{LocalObjectReference: corev1.LocalObjectReference{
							Name: stepIOType.Artifact.AccessKey.Name}, Key: stepIOType.Artifact.AccessKey.Key},
						SecretKeySecret: corev1.SecretKeySelector{LocalObjectReference: corev1.LocalObjectReference{
							Name: stepIOType.Artifact.SecretKey.Name}, Key: stepIOType.Artifact.SecretKey.Key},
					},
					Key: stepIOType.Artifact.RemotePath,
				}}
			}

			inputs.Artifacts = append(inputs.Artifacts, wfv1.Artifact{
				Name:             stepIOType.Artifact.GetName(),
				Path:             stepIOType.Artifact.GetLocalPath(),
				From:             stepIOType.Artifact.GetValue(),
				ArtifactLocation: artifactLocation,
				GlobalName:       stepIOType.Artifact.GetGlobalName(),
			})
		}
	}
	var outputs wfv1.Outputs
	for _, output := range template.GetOutputs() {
		switch stepIOType := output.GetStepIo().(type) {
		case *pb.StepIO_Parameter:
			inputs.Parameters = append(inputs.Parameters, wfv1.Parameter{
				Name:       stepIOType.Parameter.GetName(),
				Value:      &stepIOType.Parameter.Value,
				GlobalName: stepIOType.Parameter.GlobalName,
			})
		case *pb.StepIO_Artifact:
			artifactLocation := wfv1.ArtifactLocation{}

			if stepIOType.Artifact.Type == "OSS" {
				artifactLocation = wfv1.ArtifactLocation{OSS: &wfv1.OSSArtifact{
					OSSBucket: wfv1.OSSBucket{
						Endpoint: stepIOType.Artifact.Endpoint,
						Bucket:   stepIOType.Artifact.Bucket,
						AccessKeySecret: corev1.SecretKeySelector{LocalObjectReference: corev1.LocalObjectReference{
							Name: stepIOType.Artifact.AccessKey.Name}, Key: stepIOType.Artifact.AccessKey.Key},
						SecretKeySecret: corev1.SecretKeySelector{LocalObjectReference: corev1.LocalObjectReference{
							Name: stepIOType.Artifact.SecretKey.Name}, Key: stepIOType.Artifact.SecretKey.Key},
					},
					Key: stepIOType.Artifact.RemotePath,
				}}
			} else if stepIOType.Artifact.Type == "S3" {
				artifactLocation = wfv1.ArtifactLocation{S3: &wfv1.S3Artifact{
					S3Bucket: wfv1.S3Bucket{
						Endpoint: stepIOType.Artifact.Endpoint,
						Bucket:   stepIOType.Artifact.Bucket,
						AccessKeySecret: corev1.SecretKeySelector{LocalObjectReference: corev1.LocalObjectReference{
							Name: stepIOType.Artifact.AccessKey.Name}, Key: stepIOType.Artifact.AccessKey.Key},
						SecretKeySecret: corev1.SecretKeySelector{LocalObjectReference: corev1.LocalObjectReference{
							Name: stepIOType.Artifact.SecretKey.Name}, Key: stepIOType.Artifact.SecretKey.Key},
					},
					Key: stepIOType.Artifact.RemotePath,
				}}
			}

			outputs.Artifacts = append(outputs.Artifacts, wfv1.Artifact{
				Name:             stepIOType.Artifact.GetName(),
				Path:             stepIOType.Artifact.GetLocalPath(),
				From:             stepIOType.Artifact.GetValue(),
				ArtifactLocation: artifactLocation,
				GlobalName:       stepIOType.Artifact.GetGlobalName(),
			})
		}
	}
	return inputs, outputs
}
