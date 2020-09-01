import couler.argo as couler
from couler.tests.argo_yaml_test import ArgoYamlTest


def random_code():
    import random

    result = "heads" if random.randint(0, 1) == 0 else "tails"
    print(result)


def flip_coin():
    return couler.run_script(image="python:3.6", source=random_code)


class RecursionTest(ArgoYamlTest):
    def test_while(self):
        couler.exec_while(couler.equal("tails"), lambda: flip_coin())
        self.check_argo_yaml("while_golden.yaml")

    def test_while_condition_callable(self):
        cls = self.create_callable_cls(lambda: "tails")
        instance = cls()
        func_names = ["a", "b", "c", "self"]
        for func_name in func_names:
            if func_name == "self":
                couler.exec_while(couler.equal(instance), lambda: flip_coin())
            else:
                couler.exec_while(
                    couler.equal(getattr(instance, func_name)),
                    lambda: flip_coin(),
                )
            self.check_argo_yaml("while_golden.yaml")
            couler._cleanup()

    def test_while_callable(self):
        cls = self.create_callable_cls(lambda: flip_coin())
        instance = cls()
        func_names = ["a", "b", "c", "self"]
        for func_name in func_names:
            if func_name == "self":
                couler.exec_while(couler.equal("tails"), instance)
            else:
                couler.exec_while(
                    couler.equal("tails"), getattr(instance, func_name)
                )

            self.check_argo_yaml("while_golden.yaml")
            couler._cleanup()
