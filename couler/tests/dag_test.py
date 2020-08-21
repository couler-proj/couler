import couler.argo as couler
from couler.tests.argo_yaml_test import ArgoYamlTest

_test_data_dir = "test_data"
couler.config_workflow(name="pytest")


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


class DAGTest(ArgoYamlTest):
    def test_input_dag_linear(self):
        #  A
        # / \
        # B  C
        # /
        # D
        couler.dag(
            [
                [lambda: job_a(message="A")],
                [
                    lambda: job_a(message="A"),
                    lambda: job_b(message="B"),
                ],  # A -> B
                [
                    lambda: job_a(message="A"),
                    lambda: job_c(message="C"),
                ],  # A -> C
                [
                    lambda: job_b(message="B"),
                    lambda: job_d(message="D"),
                ],  # B -> D
            ]
        )

        self.check_argo_yaml("dag_golden_1.yaml")

    def test_set_dependencies(self):
        couler.set_dependencies(lambda: job_a(message="A"), dependencies=None)
        couler.set_dependencies(lambda: job_b(message="B"), dependencies=["A"])
        couler.set_dependencies(lambda: job_c(message="C"), dependencies=["A"])
        couler.set_dependencies(lambda: job_d(message="D"), dependencies=["B"])

        self.check_argo_yaml("dag_golden_1.yaml")
        couler._cleanup()

    def test_set_dependencies_with_passing_parameter_artifact_implicitly(self):
        def producer_two(step_name):
            output_one = couler.create_parameter_artifact(path="/tmp/t1.txt")
            output_two = couler.create_parameter_artifact(path="/tmp/t2.txt")
            c1 = "echo -n A > %s" % output_one.path
            c2 = "echo -n B > %s" % output_two.path
            command = "%s && %s" % (c1, c2)
            return couler.run_container(
                image="docker/whalesay:latest",
                args=command,
                output=[output_one, output_two],
                command=["bash", "-c"],
                step_name=step_name,
            )

        def consume_two(step_name):
            couler.run_container(
                image="docker/whalesay:latest",
                command=["echo"],
                args=["--input: x"],
                step_name=step_name,
            )

        couler.set_dependencies(
            lambda: producer_two(step_name="A"), dependencies=None
        )
        couler.set_dependencies(
            lambda: consume_two(step_name="B"), dependencies=["A"]
        )

        self.check_argo_yaml("parameter_passing_golden.yaml")
        couler._cleanup()

    # TODO: Provide new test case without `tf.train`.
    # def test_set_dependencies_for_job(self):
    #
    #     def producer_two(step_name):
    #         output_one = couler.create_parameter_artifact(path="/tmp/t1.txt")
    #         output_two = couler.create_parameter_artifact(path="/tmp/t2.txt")
    #         c1 = "echo -n A > %s" % output_one.path
    #         c2 = "echo -n B > %s" % output_two.path
    #         command = "%s && %s" % (c1, c2)
    #         return couler.run_container(
    #             image="docker/whalesay:latest",
    #             args=command,
    #             output=[output_one, output_two],
    #             command=["bash", "-c"],
    #             step_name=step_name,
    #         )
    #
    #     def train_1(step_name):
    #         tf.train(
    #             num_ps=2,
    #             num_workers=3,
    #             image="tensorflow:1.13",
    #             command="python tf.py",
    #             clean_pod_policy="Running",
    #             step_name=step_name,
    #         )
    #
    #     def train_2(step_name):
    #         tf.train(
    #             num_ps=2,
    #             num_workers=3,
    #             image="tensorflow:1.13",
    #             command="python tf.py",
    #             clean_pod_policy="Running",
    #             step_name=step_name,
    #         )
    #
    #     couler.set_dependencies(
    #         lambda: producer_two(step_name="A"), dependencies=None
    #     )
    #     couler.set_dependencies(
    #         lambda: train_1(step_name="B"), dependencies=["A"]
    #     )
    #     couler.set_dependencies(
    #         lambda: train_2(step_name="C"), dependencies=["B"]
    #     )
