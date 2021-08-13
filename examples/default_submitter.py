import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter

submitter = ArgoSubmitter(namespace="my_namespace")

# Instead of setting up and passing a submitter each time,
# you can just set it as default!
couler.set_default_submitter(submitter)

couler.run_container(
    image="docker/whalesay",
    command=["cowsay"],
    args=["hello world with default submitter"],
)
# no submitter need be passed now!
couler.run()

couler.run_container(
    image="docker/whalesay",
    command=["cowsay"],
    args=["yet another hello world with default submitter"],
)
# You can still pass a submitter to use,
# overriding the default submitter if you want to
couler.run(ArgoSubmitter(namespace="other_namespace"))
