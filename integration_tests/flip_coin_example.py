import time

import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter


def random_code():
    import random

    res = "heads" if random.randint(0, 1) == 0 else "tails"
    print(res)


def flip_coin():
    return couler.run_script(image="python:alpine3.6", source=random_code)


def heads():
    return couler.run_container(
        image="alpine:3.6", command=["sh", "-c", 'echo "it was heads"']
    )


def tails():
    return couler.run_container(
        image="alpine:3.6", command=["sh", "-c", 'echo "it was tails"']
    )


if __name__ == "__main__":
    couler.config_workflow(timeout=3600, time_to_clean=3600 * 1.5)

    result = flip_coin()
    couler.when(couler.equal(result, "heads"), lambda: heads())
    couler.when(couler.equal(result, "tails"), lambda: tails())

    submitter = ArgoSubmitter(namespace="argo")
    wf = couler.run(submitter=submitter)
    wf_name = wf["metadata"]["name"]
    print("Workflow %s has been submitted" % wf_name)

    print(couler.workflow_yaml())
    time.sleep(10)

    # TODO(terrytangyuan): Validate status before deleting
    # print("Deleting workflow %s" % wf_name)
    # couler.delete(wf_name, namespace="argo", grace_period_seconds=10)
    # print("Workflow %s has been deleted" % wf_name)
