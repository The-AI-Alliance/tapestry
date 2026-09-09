import importlib.util
import unittest

NUMPY_AVAILABLE = importlib.util.find_spec("numpy") is not None

if NUMPY_AVAILABLE:
    from wan_spike.task import make_ndarrays, total_bytes, validate_positive_int


@unittest.skipUnless(NUMPY_AVAILABLE, "wan_spike task tests require numpy")
class TaskTest(unittest.TestCase):
    def test_make_ndarrays_chunks_payload_and_reports_bytes(self):
        arrays = make_ndarrays(payload_params=7, tensor_params=3, seed=11)

        self.assertEqual([array.shape for array in arrays], [(3,), (3,), (1,)])
        self.assertTrue(all(array.dtype.name == "float16" for array in arrays))
        self.assertEqual(total_bytes(arrays), 14)

    def test_validate_positive_int_rejects_non_positive_values(self):
        cases = [
            ("payload_params", 0),
            ("payload_params", -1),
            ("tensor_params", 0),
        ]

        for name, value in cases:
            with (
                self.subTest(name=name, value=value),
                self.assertRaisesRegex(ValueError, f"{name} must be positive"),
            ):
                validate_positive_int(name, value)


if __name__ == "__main__":
    unittest.main()
