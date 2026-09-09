"""Test-only import stubs for optional local-model dependencies.

The task environment intentionally has no completed application virtualenv.
These modules are only imported by the unexercised production download path;
tests replace their runtime behavior with fakes.
"""

import sys
from types import ModuleType

if "huggingface_hub" not in sys.modules:
    huggingface_hub = ModuleType("huggingface_hub")
    huggingface_hub.hf_hub_download = lambda **_: ""
    sys.modules["huggingface_hub"] = huggingface_hub

if "llama_cpp" not in sys.modules:
    llama_cpp = ModuleType("llama_cpp")

    class Llama:
        def __init__(self, **_: object) -> None:
            pass

    llama_cpp.Llama = Llama
    sys.modules["llama_cpp"] = llama_cpp


if "python_multipart" not in sys.modules:
    python_multipart = ModuleType("python_multipart")
    multipart_module = ModuleType("python_multipart.multipart")

    def parse_options_header(value: bytes | str | None) -> tuple[bytes, dict[bytes, bytes]]:
        raw = value.encode("latin-1") if isinstance(value, str) else value or b""
        pieces = raw.split(b";")
        options: dict[bytes, bytes] = {}
        for piece in pieces[1:]:
            key, separator, item = piece.strip().partition(b"=")
            if separator:
                options[key.lower()] = item.strip().strip(b'"')
        return pieces[0].strip().lower(), options

    class MultipartParser:
        def __init__(self, boundary: bytes, callbacks: dict[str, object]) -> None:
            self.boundary = boundary
            self.callbacks = callbacks
            self.buffer = bytearray()
            self.parsed = False

        def write(self, data: bytes) -> None:
            self.buffer.extend(data)
            if b"--" + self.boundary + b"--" in self.buffer:
                self._parse()

        def finalize(self) -> None:
            self._parse()

        def _parse(self) -> None:
            if self.parsed:
                return
            self.parsed = True
            marker = b"--" + self.boundary
            for part in bytes(self.buffer).split(marker)[1:]:
                part = part.strip(b"\r\n")
                if not part or part == b"--":
                    continue
                headers, _, body = part.partition(b"\r\n\r\n")
                self.callbacks["on_part_begin"]()  # type: ignore[operator]
                for header in headers.split(b"\r\n"):
                    name, _, value = header.partition(b":")
                    self.callbacks["on_header_field"](name, 0, len(name))  # type: ignore[operator]
                    value = value.strip()
                    self.callbacks["on_header_value"](
                        value, 0, len(value)
                    )  # type: ignore[operator]
                    self.callbacks["on_header_end"]()  # type: ignore[operator]
                self.callbacks["on_headers_finished"]()  # type: ignore[operator]
                if body:
                    self.callbacks["on_part_data"](body, 0, len(body))  # type: ignore[operator]
                self.callbacks["on_part_end"]()  # type: ignore[operator]
            self.callbacks["on_end"]()  # type: ignore[operator]

    python_multipart.__version__ = "0.0.14"
    python_multipart.MultipartParser = MultipartParser
    multipart_module.parse_options_header = parse_options_header
    sys.modules["python_multipart"] = python_multipart
    sys.modules["python_multipart.multipart"] = multipart_module
