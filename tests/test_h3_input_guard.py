import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).parents[1] / "helpers" / "h3_input_guard.py"
spec = importlib.util.spec_from_file_location("h3_input_guard", MODULE_PATH)
h3_input_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h3_input_guard)


class H3InputGuardTest(unittest.TestCase):
    @staticmethod
    def valid_kwargs(**overrides):
        values = {
            "source_width": 1920,
            "source_height": 1080,
            "source_fps": 24.0,
            "duration": 4.0,
            "output_width": 1376,
            "output_height": 768,
            "length": 107,
            "reference_batch": 1,
            "reference_width": 2048,
            "reference_height": 1024,
        }
        values.update(overrides)
        return values

    def test_accepts_a6000_safe_boundary(self):
        h3_input_guard.validate_h3_inputs(
            source_width=1920,
            source_height=1080,
            source_fps=24.0,
            duration=4.0,
            output_width=1376,
            output_height=768,
            length=107,
            reference_batch=1,
            reference_width=2048,
            reference_height=1024,
        )

    def test_rejects_each_unsafe_dimension_with_actionable_message(self):
        cases = [
            ({"source_width": 3840}, "source video resolution"),
            ({"source_fps": 30.0}, "source video frame rate"),
            ({"duration": 4.01}, "duration"),
            ({"output_width": 1920, "output_height": 1080}, "output resolution"),
            ({"length": 108}, "frame count"),
            ({"reference_batch": 2}, "reference image count"),
            ({"reference_width": 2049}, "reference image size"),
        ]
        defaults = {
            "source_width": 1920,
            "source_height": 1080,
            "source_fps": 24.0,
            "duration": 4.0,
            "output_width": 1376,
            "output_height": 768,
            "length": 107,
            "reference_batch": 1,
            "reference_width": 2048,
            "reference_height": 1024,
        }

        for overrides, expected in cases:
            with self.subTest(overrides=overrides):
                values = defaults | overrides
                with self.assertRaisesRegex(ValueError, expected):
                    h3_input_guard.validate_h3_inputs(**values)

    def test_rejects_portrait_source_larger_than_1080_by_1920(self):
        with self.assertRaisesRegex(ValueError, "source video resolution"):
            h3_input_guard.validate_h3_inputs(
                source_width=1200,
                source_height=1920,
                source_fps=24.0,
                duration=4.0,
                output_width=768,
                output_height=1376,
                length=107,
                reference_batch=1,
                reference_width=1024,
                reference_height=2048,
            )
    def test_rejects_non_positive_values_even_if_widget_constraints_are_bypassed(self):
        with self.assertRaisesRegex(ValueError, "dimensions must be positive"):
            h3_input_guard.validate_h3_inputs(**self.valid_kwargs(output_width=0))

    def test_runtime_node_returns_the_validated_inputs_unchanged(self):
        video = object()
        image = type("Image", (), {"shape": (1, 1024, 1024, 3)})()
        node = h3_input_guard.RunComfyH3A6000InputGuard()
        original_probe = h3_input_guard._read_video_metadata
        try:
            h3_input_guard._read_video_metadata = lambda _video: (1920, 1080, 24.0)
            result = node.run(video, image, 4.0, 1024, 1024, 107)
        finally:
            h3_input_guard._read_video_metadata = original_probe
        self.assertEqual((video, image, 4.0, 1024, 1024, 107), result)
        self.assertIn(
            "RunComfyH3A6000InputGuard", h3_input_guard.NODE_CLASS_MAPPINGS
        )


if __name__ == "__main__":
    unittest.main()
