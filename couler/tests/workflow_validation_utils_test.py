import couler.argo as couler
from couler.core.workflow_validation_utils import (  # noqa: F401
    validate_workflow_yaml,
)
from couler.tests.argo_yaml_test import ArgoYamlTest


def start_pod(message):
    return couler.run_container(
        image="couler/python:3.6",
        command=["bash", "-c", "mkdir /home/admin/logs/ | echo"],
        args=[message],
    )


def start_pod_with_step(message, step_name):
    return couler.run_container(
        image="couler/python:3.6",
        command=["bash", "-c", "mkdir /home/admin/logs/ | echo"],
        args=[message],
        step_name=step_name,
    )


def run_multiple_pods(num_pods):
    para = []
    i = 0
    while i < num_pods:
        message = "couler-pod-%s" % i
        para.append(message)
        i = i + 1
    couler.map(lambda x: start_pod(x), para)


class WorkflowValidationUtilsTest(ArgoYamlTest):
    # TODO: Need to test this with Argo as a dependency
    # def test_validate_workflow_multiple_pods(self):
    #     run_multiple_pods(2)
    #     wf = couler.workflow_yaml()
    #     validate_workflow_yaml(wf)
    #
    #     wf2 = copy.deepcopy(wf)
    #     del wf2["spec"]
    #     self.assertRaisesRegex(
    #         Exception,
    #         "Workflow yaml must contain spec.templates",
    #         validate_workflow_yaml,
    #         wf2,
    #     )
    #
    #     wf4 = copy.deepcopy(wf)
    #     wf4["spec"]["templates"][0]["steps"] = None
    #     self.assertRaisesRegex(
    #         Exception,
    #         "At least one step definition must exist in steps",
    #         validate_workflow_yaml,
    #         wf4,
    #     )
    #
    #     couler._cleanup()

    # TODO: Provide new test case without `tf.train`.
    # def test_validate_cron_workflow_run_multiple_jobs(self):
    #     run_multiple_jobs(2)
    #     couler.config_workflow(
    #         cron_config={"schedule": "1 0 * * *", "suspend": "false"}
    #     )
    #     wf = couler.workflow_yaml()
    #     validate_workflow_yaml(wf)
    #
    #     wf2 = copy.deepcopy(wf)
    #     del wf2["spec"]["workflowSpec"]["templates"]
    #     self.assertRaisesRegex(
    #         Exception,
    #         "CronWorkflow yaml must contain spec.workflowSpec.templates",
    #         validate_workflow_yaml,
    #         wf2,
    #     )
    #     couler._cleanup()

    # TODO: Provide new test case without `tf.train`.
    # def test_validate_workflow_run_multiple_jobs(self):
    #     run_multiple_jobs(2)
    #     validate_workflow_yaml(couler.workflow_yaml())
    #     couler._cleanup()

    # TODO: Provide new test case without `tf.train`.
    # def test_validate_workflow_run_dag_jobs(self):
    #     run_dag_jobs()
    #     wf = couler.workflow_yaml()
    #     validate_workflow_yaml(wf)
    #
    #     wf2 = copy.deepcopy(wf)
    #     wf2["spec"]["templates"][0]["dag"] = None
    #     self.assertRaisesRegex(
    #         Exception,
    #         "At least one task definition must exist in dag.tasks",
    #         validate_workflow_yaml,
    #         wf2,
    #     )
    #     couler._cleanup()

    def test_validate_step_name(self):
        start_pod_with_step(message="abc", step_name="a_b")
        wf = couler.workflow_yaml()
        self.assertEqual(wf["spec"]["templates"][1]["name"], "a-b")
        couler._cleanup()
