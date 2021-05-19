module github.com/couler-proj/couler

go 1.13

require (
	github.com/alecthomas/assert v0.0.0-20170929043011-405dbfeb8e38
	github.com/alecthomas/colour v0.1.0 // indirect
	github.com/alecthomas/repr v0.0.0-20201120212035-bb82daffcca2 // indirect
	github.com/argoproj/argo v0.0.0-20210125193418-4cb5b7eb8075
	github.com/golang/protobuf v1.4.3
	github.com/google/go-cmp v0.5.2 // indirect
	github.com/mattn/go-isatty v0.0.12 // indirect
	golang.org/x/crypto v0.0.0-20200622213623-75b288015ac9 // indirect
	golang.org/x/lint v0.0.0-20210508222113-6edffad5e616 // indirect
	golang.org/x/text v0.3.4 // indirect
	golang.org/x/tools v0.1.1 // indirect
	google.golang.org/protobuf v1.25.0 // indirect
	k8s.io/api v0.18.2
	k8s.io/apimachinery v0.18.2
	k8s.io/client-go v0.18.2
	k8s.io/kube-openapi v0.0.0-20201113171705-d219536bb9fd // indirect
)

replace (
	k8s.io/api => k8s.io/api v0.17.8
	k8s.io/apimachinery => k8s.io/apimachinery v0.17.8
	k8s.io/client-go => k8s.io/client-go v0.17.8
)
