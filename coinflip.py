import couler.argo as couler
# from couler.argo_submitter import ArgoSubmitter
from couler.docker_submitter import DockerSubmitter

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


# result = flip_coin()
# couler.when(couler.equal(result, "heads"), lambda: heads())
# couler.when(couler.equal(result, "tails"), lambda: tails())

submitter = DockerSubmitter()
submitter.run_docker_container()
# couler.run(submitter=submitter)
# cluster_config = "/Users/wei.yan/workspace/src/gitlab.alipay.net/ant-aii/couler/ant_couler/clusters/sigma_eu95.py"

# couler.config_workflow(
#     name="demo",
#     user_id="123456",
#     timeout=3600,
#     time_to_clean=6000 * 4,
#     cluster_config_file=cluster_config,
# )
