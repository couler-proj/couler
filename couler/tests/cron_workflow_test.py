import couler.argo as couler
from couler.tests.argo_yaml_test import ArgoYamlTest


_test_data_dir = "test_data"


class CronJobTest(ArgoYamlTest):
    def test_cron_workflow(self):
        def tails():
            return couler.run_container(
                image="python:3.6",
                command=["bash", "-c", 'echo "run schedule job"'],
            )

        tails()

        # schedule to run at one minute past midnight (00:01) every day
        cron_config = {"schedule": "1 0 * * *", "suspend": "false"}

        couler.config_workflow(name="pytest", cron_config=cron_config)

        self.check_argo_yaml("cron_workflow_golden.yaml")
