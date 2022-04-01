import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter
from couler.core.templates.toleration import Toleration

def job(name):
    # Define a nodes Toleration
    toleration = Toleration(
        key='<key>', 
        operator='<operator>', # Exists
        effect='<effect>', # NoSchedule, NoExecute, PreferNoSchedule
    )
    # Add the toleration to the workflow
    couler.add_toleration(toleration) # pipeline/nodepool=pipe:NoSchedule
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[name],
        step_name=name,
        node_selector={'<key>':'<value>'}
    )


#     A
#    / \
#   B   C
#  /
# D
def linear():
    couler.set_dependencies(lambda: job(name="A"), dependencies=None)
    couler.set_dependencies(lambda: job(name="B"), dependencies=["A"])
    couler.set_dependencies(lambda: job(name="C"), dependencies=["A"])
    couler.set_dependencies(lambda: job(name="D"), dependencies=["B"])


#   A
#  / \
# B   C
#  \ /
#   D
def diamond():
    couler.dag(
        [
            [lambda: job(name="A")],
            [lambda: job(name="A"), lambda: job(name="B")],  # A -> B
            [lambda: job(name="A"), lambda: job(name="C")],  # A -> C
            [lambda: job(name="B"), lambda: job(name="D")],  # B -> D
            [lambda: job(name="C"), lambda: job(name="D")],  # C -> D
        ]
    )


linear()
submitter = ArgoSubmitter(namespace='<nodepool_namespace>')
couler.run(submitter=submitter)
