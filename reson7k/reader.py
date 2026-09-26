from __future__ import annotations

import calendar
import logging
import os
import struct
import time
from collections import Counter
from pathlib import Path

from .datagrams import ResonDatagrams, parse

logger = logging.getLogger(__name__)


class Reson:
    """Lightweight reader for selected Teledyne RESON S7K records."""

    HEADER_SIZE = 64
    HEADER_FORMAT = "<2H4I2Hf2BH2I2HI2H3I"
    FOOTER_SIZE = 4
    SYNC_PATTERN = 65535

    def __init__(self, input_path: str | Path):
        self.path = Path(input_path)
        self.file = None
        self.file_length = 0
        self.file_location = 0
        self.file_end = False
        self.map: dict[int, list[tuple[int, float, int, int]]] = {}
        self.mapped = False
        self._valid = self._open_file()

    @property
    def valid(self) -> bool:
        return self._valid

    def _open_file(self) -> bool:
        if self.path.suffix.lower() != ".s7k":
            raise ValueError("Expected a .s7k file")
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        self.file = self.path.open("rb")
        self.file_length = os.stat(self.path).st_size
        return True

    def close(self) -> None:
        if self.file and not self.file.closed:
            self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def read_dg_header(self, count: int = 0):
        while True:
            start = self.file.tell()
            chunk = self.file.read(self.HEADER_SIZE)
            self.file_location = self.file.tell()
            if len(chunk) != self.HEADER_SIZE:
                return None, count

            header = struct.unpack(self.HEADER_FORMAT, chunk)
            record_size = header[3]
            if (header[2] == self.SYNC_PATTERN
                    and self.HEADER_SIZE + self.FOOTER_SIZE <= record_size
                    and start + record_size <= self.file_length):
                self.file.seek(start + record_size)
                return header, count
            self.file.seek(start + 1)
            count += 1

    def data_map(self, force: bool = False):
        if self.mapped and not force:
            return self.map

        self.file.seek(0)
        self.file_end = False
        dg_map = {}

        while not self.file_end:
            header, shifted = self.read_dg_header()
            if shifted:
                logger.warning("Sync pattern realigned by %d byte(s)", shifted)
            if header is None:
                self.file_end = True
                break

            dg_type = header[12]
            optional_offset = header[4]
            dg_time = self.get_time(header[6], header[7], header[9], header[10], header[8])
            data_header_location = self.file_location
            data_size = header[3] - self.HEADER_SIZE - self.FOOTER_SIZE
            dg_map.setdefault(dg_type, []).append(
                (data_header_location, dg_time, data_size, optional_offset)
            )

        self.map = dg_map
        self.mapped = True
        return dg_map

    def record_summary(self) -> dict[int, int]:
        self.data_map()
        return dict(sorted((code, len(records)) for code, records in self.map.items()))

    def get_datagram(self, dg_type: ResonDatagrams, dg_record_range=None):
        self.data_map()
        dg_code = dg_type.value
        if dg_code not in self.map:
            return []

        total = len(self.map[dg_code])
        indices = range(total) if dg_record_range is None else dg_record_range
        output = []
        for index in indices:
            if index < 0 or index >= total:
                raise IndexError(f"Record index {index} outside 0..{total - 1}")
            location, dg_time, dg_size, _ = self.map[dg_code][index]
            packet = self.get_record(dg_type, location, dg_size)
            packet.time = dg_time
            output.append(packet)
        return output

    def get_record(self, dg_type: ResonDatagrams, location: int, size: int):
        self.file.seek(location)
        chunk = self.file.read(size)
        if len(chunk) != size:
            raise EOFError(f"Expected {size} bytes but read {len(chunk)}")
        return parse(chunk, dg_type)

    @staticmethod
    def get_time(year, day, hour, minute, second) -> float:
        time_fmt = "%Y, %j, %H, %M"
        temp = f"{year}, {day}, {hour}, {minute}"
        timestruct = time.strptime(temp, time_fmt)
        return (calendar.timegm(timestruct) + second) * 1000
