package submitter

import (
	"fmt"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/fields"
	"k8s.io/client-go/tools/clientcmd"

	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	wfclientset "github.com/argoproj/argo/pkg/client/clientset/versioned"
)

// ArgoWorkflowSubmitter holds configurations used for workflow submission
type ArgoWorkflowSubmitter struct {
	namespace      string
	kubeConfigPath string
}

// Submit takes an Argo Workflow object and submit it to Kubernetes cluster
func (submitter *ArgoWorkflowSubmitter) Submit(wf wfv1.Workflow, watch bool) (*wfv1.Workflow, error) {
	// Use the current context in kubeconfig
	config, err := clientcmd.BuildConfigFromFlags("", submitter.kubeConfigPath)
	if err != nil {
		return nil, fmt.Errorf("failed to get the current context in the kubeconfig file %s: %s", submitter.kubeConfigPath, err)
	}

	// Create the workflow client
	wfClient := wfclientset.NewForConfigOrDie(config).ArgoprojV1alpha1().Workflows(submitter.namespace)

	// Submit the workflow
	createdWf, err := wfClient.Create(&wf)
	if err != nil {
		return createdWf, fmt.Errorf("failed to create the workflow %s: %s", wf.Name, err)
	}
	fmt.Printf("Workflow %s successfully submitted\n", createdWf.Name)

	if watch {
		// Wait for the workflow to complete
		fieldSelector := fields.ParseSelectorOrDie(fmt.Sprintf("metadata.name=%s", createdWf.Name))
		watchIf, err := wfClient.Watch(metav1.ListOptions{FieldSelector: fieldSelector.String()})
		if err != nil {
			return createdWf, fmt.Errorf("failed establish a watch")
		}
		defer watchIf.Stop()
		for next := range watchIf.ResultChan() {
			wf, ok := next.Object.(*wfv1.Workflow)
			if !ok {
				continue
			}
			if !wf.Status.FinishedAt.IsZero() {
				fmt.Printf("Workflow %s %s at %v. Message: %s\n", wf.Name, wf.Status.Phase, wf.Status.FinishedAt, wf.Status.Message)
				if wf.Status.Phase == wfv1.NodeFailed || wf.Status.Phase == wfv1.NodeError {
					for _, node := range wf.Status.Nodes {
						fmt.Printf("Workflow node %s %s. Message: %s\n", node.Name, node.Phase, node.Message)
					}
				}
				createdWf = wf
				break
			}
		}
	}
	return createdWf, nil
}
