import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter

couler.run_container(
    image="docker/whalesay", command=["cowsay"], args=["hello world"]
)

submitter = ArgoSubmitter()
result = couler.run(submitter=submitter)

# Instead of passing the submitter each time, you can just set it as default!
ArgoSubmitter.set_default(submitter)

couler.run_container(
    image="docker/whalesay",
    command=["cowsay"],
    args=["hello world with default submitter"],
)

result_with_default_submitter = (
    couler.run()
)  # no submitter need be passed now!

couler.run_container(
    image="docker/whalesay",
    command=["cowsay"],
    args=["hello world with default submitter 2"],
)

result_with_default_submitter_2 = (
    couler.run()
)  # no submitter need be passed now either!
