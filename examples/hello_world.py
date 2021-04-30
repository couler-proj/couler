import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter

couler.run_container(
    image="docker/whalesay", command=["cowsay"], args=["hello world"]
)

submitter = ArgoSubmitter()
result = couler.run(submitter=submitter)
