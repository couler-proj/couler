import couler.argo as couler
from couler.tests.argo_yaml_test import ArgoYamlTest
import random


def random_code():
    result = "heads" if random.randint(0, 1) == 0 else "tails"
    print(result)


def flip_coin():
    return couler.run_script(image="python:3.6", source=random_code)


class RecursionTest(ArgoYamlTest):
    def test_while(self):
        couler.exec_while(couler.equal("tails"), lambda: flip_coin())
        self.check_argo_yaml("while_golden.yaml")
