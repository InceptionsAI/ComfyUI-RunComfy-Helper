from __future__ import annotations

import math
from typing import Any


MAX_SOURCE_LONG_EDGE = 1920
MAX_SOURCE_SHORT_EDGE = 1080
MAX_SOURCE_FPS = 24.0
MAX_DURATION_SECONDS = 4.0
MAX_OUTPUT_PIXELS = 1_100_000  # 1 MP preset plus 32-pixel alignment.
MAX_FRAME_COUNT = 107
MAX_REFERENCE_IMAGES = 1
MAX_REFERENCE_EDGE = 2048


def validate_h3_inputs(
    *,
    source_width: int,
    source_height: int,
    source_fps: float,
    duration: float,
    output_width: int,
    output_height: int,
    length: int,
    reference_batch: int,
    reference_width: int,
    reference_height: int,
) -> None:
    """Reject inputs outside the conservative A6000 envelope for workflow 1500."""
    errors: list[str] = []
    source_long, source_short = sorted((source_width, source_height), reverse=True)

    if source_width <= 0 or source_height <= 0:
        errors.append("source video dimensions must be positive")
    elif source_long > MAX_SOURCE_LONG_EDGE or source_short > MAX_SOURCE_SHORT_EDGE:
        errors.append(
            "source video resolution must be at most 1920x1080 (or 1080x1920)"
        )
    if not math.isfinite(source_fps) or source_fps <= 0 or source_fps > MAX_SOURCE_FPS:
        errors.append("source video frame rate must be greater than 0 and at most 24 FPS")
    if not math.isfinite(duration) or duration <= 0 or duration > MAX_DURATION_SECONDS:
        errors.append("duration must be greater than 0 and at most 4 seconds")
    if output_width <= 0 or output_height <= 0:
        errors.append("output dimensions must be positive")
    elif output_width * output_height > MAX_OUTPUT_PIXELS:
        errors.append("output resolution must use the 1.0 MP preset or lower")
    if length <= 0 or length > MAX_FRAME_COUNT:
        errors.append("frame count must be between 1 and 107")
    if reference_batch <= 0 or reference_batch > MAX_REFERENCE_IMAGES:
        errors.append("reference image count must be exactly 1")
    if reference_width <= 0 or reference_height <= 0:
        errors.append("reference image dimensions must be positive")
    elif max(reference_width, reference_height) > MAX_REFERENCE_EDGE:
        errors.append("reference image size must have a longest edge of at most 2048 px")

    if errors:
        detail = "; ".join(errors)
        raise ValueError(
            "MiniMax H3 A6000 input validation failed: "
            f"{detail}. Reduce the input settings before running this public "
            "A6000 workflow."
        )


def _read_video_metadata(video: Any) -> tuple[int, int, float]:
    """Read container metadata without decoding the video's frames."""
    source = video.get_stream_source()
    if hasattr(source, "seek"):
        source.seek(0)

    try:
        import av
    except ImportError as exc:  # pragma: no cover - ComfyUI provides PyAV.
        raise RuntimeError("PyAV is required to validate video metadata") from exc

    try:
        with av.open(source, mode="r") as container:
            stream = next((item for item in container.streams if item.type == "video"), None)
            if stream is None:
                raise ValueError("the selected file has no video stream")
            if stream.average_rate is None:
                raise ValueError("the selected video's frame rate could not be determined")
            return int(stream.width), int(stream.height), float(stream.average_rate)
    finally:
        if hasattr(source, "seek"):
            source.seek(0)


def _read_reference_shape(reference_image: Any) -> tuple[int, int, int]:
    shape = tuple(int(value) for value in reference_image.shape)
    if len(shape) != 4:
        raise ValueError("reference image must be an IMAGE batch")
    batch, height, width, _channels = shape
    return batch, width, height


class RunComfyH3A6000InputGuard:
    """Pass-through preflight guard for RunComfy's MiniMax H3 workflow."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("VIDEO",),
                "reference_image": ("IMAGE",),
                "duration": ("FLOAT", {"default": 4.0, "min": 0.1, "step": 0.1}),
                "width": ("INT", {"default": 1024, "min": 32, "step": 32}),
                "height": ("INT", {"default": 1024, "min": 32, "step": 32}),
                "length": ("INT", {"default": 107, "min": 1, "step": 1}),
            }
        }

    RETURN_TYPES = ("VIDEO", "IMAGE", "FLOAT", "INT", "INT", "INT")
    RETURN_NAMES = ("video", "reference_image", "duration", "width", "height", "length")
    FUNCTION = "run"
    CATEGORY = "RunComfy/validation"

    def run(
        self,
        video: Any,
        reference_image: Any,
        duration: float,
        width: int,
        height: int,
        length: int,
    ):
        source_width, source_height, source_fps = _read_video_metadata(video)
        reference_batch, reference_width, reference_height = _read_reference_shape(
            reference_image
        )
        validate_h3_inputs(
            source_width=source_width,
            source_height=source_height,
            source_fps=source_fps,
            duration=duration,
            output_width=width,
            output_height=height,
            length=length,
            reference_batch=reference_batch,
            reference_width=reference_width,
            reference_height=reference_height,
        )
        return video, reference_image, duration, width, height, length


NODE_CLASS_MAPPINGS = {
    "RunComfyH3A6000InputGuard": RunComfyH3A6000InputGuard,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RunComfyH3A6000InputGuard": "MiniMax H3 A6000 Input Guard (RunComfy)",
}
