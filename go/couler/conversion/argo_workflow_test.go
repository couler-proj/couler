package conversion

import (
	"testing"

	"github.com/alecthomas/assert"
	pb "github.com/couler-proj/couler/go/couler/proto/couler/v1"
)

func TestArgoWorkflowConversion(t *testing.T) {
	pbWf := &pb.Workflow{}
	pbWf.Steps = []*pb.Step{{TmplName: "whalesay", ContainerSpec: &pb.ContainerSpec{
		Image:   "docker/whalesay:latest",
		Command: []string{"cowsay", "hello world"},
	}}}

	assert.Equal(t, len(pbWf.Steps), 1)
	argoWf, err := convertToArgoWorkflow(pbWf, "hello-world-")
	assert.NoError(t, err)
	assert.Equal(t, argoWf.String(), "&Workflow{ObjectMeta:{ hello-world-     0 0001-01-01 00:00:00 +0000 UTC <nil> <nil> map[] map[] [] []  []},Spec:WorkflowSpec{Templates:[]Template{Template{Name:,Template:,Arguments:Arguments{Parameters:[]Parameter{},Artifacts:[]Artifact{},},TemplateRef:nil,Inputs:Inputs{Parameters:[]Parameter{},Artifacts:[]Artifact{},},Outputs:Outputs{Parameters:[]Parameter{},Artifacts:[]Artifact{},Result:nil,},NodeSelector:map[string]string{},Affinity:nil,Metadata:Metadata{Annotations:map[string]string{},Labels:map[string]string{},},Daemon:nil,Steps:[]ParallelSteps{},Container:nil,Script:nil,Resource:nil,DAG:nil,Suspend:nil,Volumes:[]Volume{},InitContainers:[]UserContainer{},Sidecars:[]UserContainer{},ArchiveLocation:nil,ActiveDeadlineSeconds:nil,RetryStrategy:nil,Parallelism:nil,Tolerations:[]Toleration{},SchedulerName:,PriorityClassName:,Priority:nil,ServiceAccountName:,HostAliases:[]HostAlias{},SecurityContext:nil,PodSpecPatch:,AutomountServiceAccountToken:nil,Executor:nil,},Template{Name:whalesay,Template:,Arguments:Arguments{Parameters:[]Parameter{},Artifacts:[]Artifact{},},TemplateRef:nil,Inputs:Inputs{Parameters:[]Parameter{},Artifacts:[]Artifact{},},Outputs:Outputs{Parameters:[]Parameter{},Artifacts:[]Artifact{},Result:nil,},NodeSelector:map[string]string{},Affinity:nil,Metadata:Metadata{Annotations:map[string]string{},Labels:map[string]string{},},Daemon:nil,Steps:[]ParallelSteps{},Container:&v1.Container{Name:,Image:docker/whalesay:latest,Command:[cowsay hello world],Args:[],WorkingDir:,Ports:[]ContainerPort{},Env:[]EnvVar{},Resources:ResourceRequirements{Limits:ResourceList{},Requests:ResourceList{},},VolumeMounts:[]VolumeMount{},LivenessProbe:nil,ReadinessProbe:nil,Lifecycle:nil,TerminationMessagePath:,ImagePullPolicy:,SecurityContext:nil,Stdin:false,StdinOnce:false,TTY:false,EnvFrom:[]EnvFromSource{},TerminationMessagePolicy:,VolumeDevices:[]VolumeDevice{},StartupProbe:nil,},Script:nil,Resource:nil,DAG:nil,Suspend:nil,Volumes:[]Volume{},InitContainers:[]UserContainer{},Sidecars:[]UserContainer{},ArchiveLocation:nil,ActiveDeadlineSeconds:nil,RetryStrategy:nil,Parallelism:nil,Tolerations:[]Toleration{},SchedulerName:,PriorityClassName:,Priority:nil,ServiceAccountName:,HostAliases:[]HostAlias{},SecurityContext:nil,PodSpecPatch:,AutomountServiceAccountToken:nil,Executor:nil,},},Entrypoint:whalesay,Arguments:Arguments{Parameters:[]Parameter{},Artifacts:[]Artifact{},},ServiceAccountName:,Volumes:[]Volume{},VolumeClaimTemplates:[]PersistentVolumeClaim{},Parallelism:nil,ArtifactRepositoryRef:nil,Suspend:nil,NodeSelector:map[string]string{},Affinity:nil,Tolerations:[]Toleration{},ImagePullSecrets:[]LocalObjectReference{},HostNetwork:nil,DNSPolicy:nil,DNSConfig:nil,OnExit:,TTLSecondsAfterFinished:nil,ActiveDeadlineSeconds:nil,Priority:nil,SchedulerName:,PodGC:nil,PodPriorityClassName:,PodPriority:nil,HostAliases:[]HostAlias{},SecurityContext:nil,PodSpecPatch:,AutomountServiceAccountToken:nil,Executor:nil,TTLStrategy:nil,},Status:WorkflowStatus{Phase:,StartedAt:0001-01-01 00:00:00 +0000 UTC,FinishedAt:0001-01-01 00:00:00 +0000 UTC,Message:,CompressedNodes:,Nodes:Nodes{},PersistentVolumeClaims:[]Volume{},Outputs:nil,StoredTemplates:map[string]Template{},OffloadNodeStatusVersion:,},}")
}
