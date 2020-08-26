import time

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


#  A
# / \
# B  C
# /
# D
def linear_option1():
    couler.dag(
        [
            [lambda: job_a(message="A")],
            [lambda: job_a(message="A"), lambda: job_b(message="B")],  # A -> B
            [lambda: job_a(message="A"), lambda: job_c(message="C")],  # A -> C
            [lambda: job_b(message="B"), lambda: job_d(message="D")],  # B -> D
        ]
    )


def linear_option2():
    couler.set_dependencies(lambda: job_a(message="A"), dependencies=None)
    couler.set_dependencies(lambda: job_b(message="B"), dependencies=["A"])
    couler.set_dependencies(lambda: job_c(message="C"), dependencies=["A"])
    couler.set_dependencies(lambda: job_d(message="D"), dependencies=["B"])


#  A
# / \
# B  C
# \  /
#  D
def diamond():
    couler.dag(
        [
            [lambda: job_a(message="A")],
            [lambda: job_a(message="A"), lambda: job_b(message="B")],  # A -> B
            [lambda: job_a(message="A"), lambda: job_c(message="C")],  # A -> C
            [lambda: job_b(message="B"), lambda: job_d(message="D")],  # B -> D
            [lambda: job_b(message="C"), lambda: job_d(message="D")],  # C -> D
        ]
    )


if __name__ == "__main__":
    couler.config_workflow(timeout=3600, time_to_clean=3600 * 1.5)

    diamond()
    submitter = ArgoSubmitter(namespace="argo")
    wf = couler.run(submitter=submitter)
    wf_name = wf["metadata"]["name"]
    print("Workflow %s has been submitted" % wf_name)

    time.sleep(10)

    # print("Deleting workflow %s" % wf_name)
    # couler.delete(wf_name, namespace="argo", grace_period_seconds=10)
    # print("Workflow %s has been deleted" % wf_name)
