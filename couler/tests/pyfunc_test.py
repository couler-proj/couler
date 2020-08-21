import base64
import unittest

import couler.core.pyfunc as pyfunc


class PyfuncTest(unittest.TestCase):
    def test_argo_safe_name(self):
        self.assertIsNone(pyfunc.argo_safe_name(None))
        self.assertEqual(pyfunc.argo_safe_name("a_b"), "a-b")
        self.assertEqual(pyfunc.argo_safe_name("a.b"), "a-b")
        self.assertEqual(pyfunc.argo_safe_name("a_.b"), "a--b")
        self.assertEqual(pyfunc.argo_safe_name("_abc."), "-abc-")

    def test_body(self):
        # Check None
        self.assertIsNone(pyfunc.body(None))
        # A real function
        code = """
func_name = pyfunc.workflow_filename()
# Here we assume using pytest to trigger the unit tests
self.assertTrue("pytest" in func_name)
"""
        self.assertEqual(code, pyfunc.body(self.test_get_root_caller_filename))

    def test_get_root_caller_filename(self):
        func_name = pyfunc.workflow_filename()
        # Here we assume using pytest to trigger the unit tests
        self.assertTrue("pytest" in func_name)

    def test_invocation_location(self):
        def inner_func():
            func_name, _ = pyfunc.invocation_location()
            self.assertEqual("test-invocation-location", func_name)

        inner_func()

    def test_encode_base64(self):
        s = "test encode string"
        encode = pyfunc.encode_base64(s)
        decode = str(base64.b64decode(encode), "utf-8")
        self.assertEqual(s, decode)

    def test_check_gpu(self):
        with self.assertRaises(TypeError):
            pyfunc.gpu_requested("cpu=1")
        self.assertFalse(pyfunc.gpu_requested(None))
        self.assertFalse(pyfunc.gpu_requested({}))
        self.assertFalse(pyfunc.gpu_requested({"cpu": 1}))
        self.assertFalse(pyfunc.gpu_requested({"cpu": 1, "memory": 2}))
        self.assertTrue(pyfunc.gpu_requested({"gpu": 1}))
        self.assertTrue(pyfunc.gpu_requested({" gpu ": 1}))
        self.assertTrue(pyfunc.gpu_requested({"GPU": 1}))
        self.assertTrue(
            pyfunc.gpu_requested({"cpu": 1, "memory": 2, "gpu": 1})
        )

    def test_non_empty(self):
        self.assertFalse(pyfunc.non_empty(None))
        self.assertFalse(pyfunc.non_empty([]))
        self.assertFalse(pyfunc.non_empty({}))
        self.assertTrue(pyfunc.non_empty(["a"]))
        self.assertTrue(pyfunc.non_empty({"a": "b"}))
