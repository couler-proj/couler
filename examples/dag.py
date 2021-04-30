import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter


def job_a(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="A",
    )


def job_b(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="B",
    )


def job_c(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="C",
    )


def job_d(message):
    couler.run_container(
        image="docker/whalesay:latest",
        command=["cowsay"],
        args=[message],
        step_name="D",
    )


#     A
#    / \
#   B   C
#  /
# D
def linear():
    couler.set_dependencies(lambda: job_a(message="A"), dependencies=None)
    couler.set_dependencies(lambda: job_b(message="B"), dependencies=["A"])
    couler.set_dependencies(lambda: job_c(message="C"), dependencies=["A"])
    couler.set_dependencies(lambda: job_d(message="D"), dependencies=["B"])


#   A
#  / \
# B   C
#  \ /
#   D
def diamond():
    couler.dag(
        [
            [lambda: job_a(message="A")],
            [lambda: job_a(message="A"), lambda: job_b(message="B")],  # A -> B
            [lambda: job_a(message="A"), lambda: job_c(message="C")],  # A -> C
            [lambda: job_b(message="B"), lambda: job_d(message="D")],  # B -> D
            [lambda: job_c(message="C"), lambda: job_d(message="D")],  # C -> D
        ]
    )


linear()
submitter = ArgoSubmitter()
couler.run(submitter=submitter)
