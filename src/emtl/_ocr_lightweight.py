"""Frozen tiny CAPTCHA CNN: Pillow plus Python standard library, no ML runtime.

Model: emtl-captcha-tinycnn-f32-v1, 83,984 parameters; audited SHA-256
27dc2423ad452a3a723ba0d3ccc8d57a81bfda0238497baf94ce22926585cf4a.
The image pipeline and arithmetic preserve the independently tested v1 model.
"""

import base64
import io
import json
import sys
import zipfile
from array import array
from importlib import resources

from PIL import Image


def _relu(values):
    for index, value in enumerate(values):
        if value < 0.0:
            values[index] = 0.0
    return values


def _conv3_stride2(image, channels, height, width, weights, bias, out_channels):
    """Channel-first 3x3 stride-two convolution, padding one, fused ReLU."""
    out_h = (height + 1) // 2
    out_w = (width + 1) // 2
    output = []
    for out_channel in range(out_channels):
        dst = [bias[out_channel]] * (out_h * out_w)
        kernel_start = out_channel * channels * 9
        for channel in range(channels):
            src = image[channel * height * width : (channel + 1) * height * width]
            offset = kernel_start + channel * 9
            for kernel_y in range(3):
                for kernel_x in range(3):
                    value = weights[offset + kernel_y * 3 + kernel_x]
                    if abs(value) < 1e-12:
                        continue
                    for y in range(out_h):
                        source_y = 2 * y + kernel_y - 1
                        if source_y < 0 or source_y >= height:
                            continue
                        source_row = source_y * width
                        dest_row = y * out_w
                        for x in range(out_w):
                            source_x = 2 * x + kernel_x - 1
                            if 0 <= source_x < width:
                                dst[dest_row + x] += value * src[source_row + source_x]
        output.extend(_relu(dst))
    return output, out_h, out_w


def _linear(values, weights, bias, out_count):
    in_count = len(values)
    output = []
    for row in range(out_count):
        start = row * in_count
        accumulator = bias[row]
        for index in range(in_count):
            accumulator += weights[start + index] * values[index]
        output.append(accumulator)
    return output


class TinyCaptchaOCR:
    """One independent recognizer; ``classification(bytes)`` returns 4 digits."""

    def __init__(self):
        model = resources.files("emtl").joinpath("models", "tiny_captcha_model.b64")
        # ASCII packaging allows exact frozen bytes in source and wheel artifacts.
        model_bytes = base64.b64decode(model.read_bytes())
        with zipfile.ZipFile(io.BytesIO(model_bytes)) as archive:
            metadata = json.loads(archive.read("meta.json"))
            if metadata.get("format") != "emtl-captcha-tinycnn-f32-v1":
                raise ValueError("unsupported CAPTCHA model format")
            blob = archive.read("weights.bin")
        self._layers = {}
        for entry in metadata["layers"]:
            weights = array("f")
            start, count = entry["offset"], entry["length"]
            chunk = blob[start : start + 4 * count]
            if len(chunk) != 4 * count:
                raise ValueError("incomplete CAPTCHA model")
            weights.frombytes(chunk)
            if sys.byteorder != "little":
                weights.byteswap()
            self._layers[entry["name"]] = weights
        self._width, self._height = metadata["image_size"]

    def classification(self, image_bytes):
        """Decode an image and return a four-character decimal string."""
        with Image.open(io.BytesIO(image_bytes)) as image:
            resized = image.convert("RGB").resize((self._width, self._height), Image.Resampling.BILINEAR)
        raw = resized.tobytes()
        values = [(255 - raw[index]) / 255.0 for channel in range(3) for index in range(channel, len(raw), 3)]
        height, width, channels = self._height, self._width, 3
        for index, out_channels in enumerate((8, 16, 24), start=1):
            prefix = f"conv{index}"
            values, height, width = _conv3_stride2(
                values,
                channels,
                height,
                width,
                self._layers[f"{prefix}.weight"],
                self._layers[f"{prefix}.bias"],
                out_channels,
            )
            channels = out_channels
        values = _relu(_linear(values, self._layers["fc1.weight"], self._layers["fc1.bias"], 128))
        values = _linear(values, self._layers["fc2.weight"], self._layers["fc2.bias"], 40)
        return "".join(str(max(range(10), key=lambda digit: values[pos * 10 + digit])) for pos in range(4))
