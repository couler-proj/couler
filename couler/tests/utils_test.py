import base64
import unittest

from couler.core import utils


class PyfuncTest(unittest.TestCase):
    def test_argo_safe_name(self):
        self.assertIsNone(utils.argo_safe_name(None))
        self.assertEqual(utils.argo_safe_name("a_b"), "a-b")
        self.assertEqual(utils.argo_safe_name("a.b"), "a-b")
        self.assertEqual(utils.argo_safe_name("a_.b"), "a--b")
        self.assertEqual(utils.argo_safe_name("_abc."), "-abc-")

    def test_body(self):
        # Check None
        self.assertIsNone(utils.body(None))
        # A real function
        code = """
func_name = utils.workflow_filename()
# Here we assume that we are using `pytest` or `python -m pytest`
# to trigger the unit tests.
self.assertTrue(func_name in ["pytest", "runpy"])
"""
        self.assertEqual(code, utils.body(self.test_get_root_caller_filename))

    def test_get_root_caller_filename(self):
        func_name = utils.workflow_filename()
        # Here we assume that we are using `pytest` or `python -m pytest`
        # to trigger the unit tests.
        self.assertTrue(func_name in ["pytest", "runpy"])

    def test_invocation_location(self):
        def inner_func():
            func_name, _ = utils.invocation_location()
            self.assertEqual("test-invocation-location", func_name)

        inner_func()

    def test_encode_base64(self):
        s = "test encode string"
        encode = utils.encode_base64(s)
        decode = str(base64.b64decode(encode), "utf-8")
        self.assertEqual(s, decode)

    def test_non_empty(self):
        self.assertFalse(utils.non_empty(None))
        self.assertFalse(utils.non_empty([]))
        self.assertFalse(utils.non_empty({}))
        self.assertTrue(utils.non_empty(["a"]))
        self.assertTrue(utils.non_empty({"a": "b"}))
