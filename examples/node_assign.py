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
        node_selector={'<key>':'<value>'} # Node Selector
    )

def simple():
    couler.set_dependencies(lambda: job(name='Whale-Noise'), dependencies=None)

simple()

submitter = ArgoSubmitter(namespace='<nodepool_namespace>')
couler.run(submitter=submitter)
