from __future__ import annotations

import struct
from enum import Enum


class ResonDatagrams(Enum):
    POSITION = 1003
    ROLLPITCHHEAVE = 1012
    HEADING = 1013
    SONARSETTINGS = 7000
    BEAMGEO = 7004
    TVG = 7010
    BEAMFORMEDDATA = 7018
    RAWDETECTDATA = 7027
    SNIPPETDATA = 7028


class ResonData:
    def __init__(self):
        self.time = None
        self.parse_check = False


class Data1003(ResonData):
    def __init__(self, chunk):
        super().__init__()
        values = struct.unpack_from("<If3d5B", chunk)
        self.datum = "WGS" if values[0] == 0 else "Reserved"
        self.latency, self.latitude, self.longitude, self.datum_height = values[1:5]
        self.position_flag, self.qual_flag, self.position_method, self.num_of_satelites = values[5:9]
        self.parse_check = True


class Data1012(ResonData):
    def __init__(self, chunk):
        super().__init__()
        self.roll, self.pitch, self.heave = struct.unpack_from("<3f", chunk)
        self.parse_check = True


class Data1013(ResonData):
    def __init__(self, chunk):
        super().__init__()
        (self.heading,) = struct.unpack_from("<f", chunk)
        self.parse_check = True


class Data7000(ResonData):
    FORMAT = "<QIH4f2If2H5f2I5fIf3IfI8fH"

    def __init__(self, chunk):
        super().__init__()
        v = struct.unpack_from(self.FORMAT, chunk)
        self.sonar_id = v[0]
        self.ping_number = v[1]
        self.multiping_flag = v[2]
        self.frequency = v[3]
        self.sample_rate = v[4]
        self.rx_band_width = v[5]
        self.tx_pulse_width = v[6]
        self.tx_wave_form = {0: "CW", 1: "LFM"}.get(v[7], str(v[7]))
        self.tx_envelope = {0: "Tapered Rect", 1: "Tukey", 2: "Hamming", 3: "Hann", 4: "Rect"}.get(v[8], str(v[8]))
        self.max_pingrate = v[12]
        self.ping_period = v[13]
        self.range_select = v[14]
        self.power_select = v[15]
        self.gain_select = v[16]
        self.rx_beam_width = v[31]
        self.bottom_detect_range_min = v[32]
        self.bottom_detect_range_max = v[33]
        self.bottom_detect_depth_min = v[34]
        self.bottom_detect_depth_max = v[35]
        self.absorption = v[36]
        self.sound_velocity = v[37]
        self.spreading = v[38]
        self.parse_check = True


class Data7004(ResonData):
    def __init__(self, chunk):
        super().__init__()
        import numpy as np
        header_size = struct.calcsize("<QI")
        self.sonar_id, self.num_rx_beams = struct.unpack("<QI", chunk[:header_size])
        values = np.frombuffer(chunk[header_size:], dtype="<f4", count=4 * self.num_rx_beams)
        self.rx_beam_number = np.arange(self.num_rx_beams)
        self.rx_angle_vertical = values[0:self.num_rx_beams].copy()
        self.rx_angle_horizontal = values[self.num_rx_beams:2*self.num_rx_beams].copy()
        self.rx_beam_width_along = values[2*self.num_rx_beams:3*self.num_rx_beams].copy()
        self.rx_beam_width_across = values[3*self.num_rx_beams:4*self.num_rx_beams].copy()
        self.parse_check = True


class Data7010(ResonData):
    def __init__(self, chunk):
        super().__init__()
        import numpy as np
        fmt = "<QIHI8I"
        size = struct.calcsize(fmt)
        v = struct.unpack(fmt, chunk[:size])
        self.sonar_id, self.ping_number, self.multiping, self.num_samples = v[:4]
        self.tvg_curve = np.frombuffer(chunk[size:], dtype="<f4", count=self.num_samples).copy()
        self.parse_check = True


class Data7018(ResonData):
    def __init__(self, chunk):
        super().__init__()
        import numpy as np
        fmt = "<QIHHI"
        header_size = struct.calcsize(fmt)
        self.sonar_id, self.ping_number, self.multiping_sequence, self.num_beams, self.num_samples = struct.unpack(fmt, chunk[:header_size])
        reserved_size = struct.calcsize("<8I")
        self.reserved = struct.unpack("<8I", chunk[header_size:header_size + reserved_size])
        start = header_size + reserved_size
        count = self.num_samples * self.num_beams * 2
        raw = np.frombuffer(chunk[start:], dtype="<u2", count=count)
        if raw.size != count:
            raise ValueError("Incomplete Record 7018 sample data")
        samples = raw.reshape(self.num_samples, self.num_beams, 2)
        self.amplitude = samples[:, :, 0].copy()
        self.phase_raw = samples[:, :, 1].copy()
        self.parse_check = True


class Data7027(ResonData):
    def __init__(self, chunk):
        super().__init__()
        fmt = "<QIH2IBI3f15I"
        size = struct.calcsize(fmt)
        v = struct.unpack(fmt, chunk[:size])
        self.sonar_id, self.ping_number, self.multiping = v[:3]
        self.num_detect_points = v[3]
        self.data_field_size = v[4]
        self.detection_algorithm = v[5]
        self.flags = v[6]
        self.sample_rate = v[7]
        self.tx_steering_angle = v[8]
        self.rx_steering_angle = v[9]
        self.beam, self.detect_point, self.rx_angle = [], [], []
        self.beam_flag, self.quality_flag = [], []
        self.uncertainty, self.signal_strength = [], []
        data = chunk[size:]
        formats = {22: "<H2f2If", 26: "<H2f2I2f", 34: "<H2f2I4f"}
        record_fmt = formats.get(self.data_field_size)
        if record_fmt is None:
            raise ValueError(f"Unsupported 7027 data field size: {self.data_field_size}")
        for i in range(self.num_detect_points):
            start = i * self.data_field_size
            row = struct.unpack(record_fmt, data[start:start + self.data_field_size])
            self.beam.append(row[0]); self.detect_point.append(row[1]); self.rx_angle.append(row[2])
            self.beam_flag.append(row[3]); self.quality_flag.append(row[4]); self.uncertainty.append(row[5])
            self.signal_strength.append(row[6] if len(row) > 6 else float("nan"))
        self.parse_check = True


class Data7028(ResonData):
    def __init__(self, chunk):
        super().__init__()
        import numpy as np
        header_fmt = "<QI2H2BI6I"
        descriptor_fmt = "<H3I"
        header_size = struct.calcsize(header_fmt)
        descriptor_size = struct.calcsize(descriptor_fmt)
        v = struct.unpack(header_fmt, chunk[:header_size])
        self.sonar_id, self.ping_number, self.multiping, self.num_detect_points = v[:4]
        self.error_flag, self.control_flag, self.flags = v[4:7]
        self.beam_number, self.snippet_start_sample = [], []
        self.bottom_detect_sample, self.snippet_end_sample, self.snippet_samples = [], [], []
        data = chunk[header_size:]
        offset = 0
        for _ in range(self.num_detect_points):
            row = struct.unpack(descriptor_fmt, data[offset:offset + descriptor_size])
            self.beam_number.append(row[0]); self.snippet_start_sample.append(row[1])
            self.bottom_detect_sample.append(row[2]); self.snippet_end_sample.append(row[3])
            offset += descriptor_size
        # Preserve the original project's interpretation of the flags until validated.
        bytes_per_sample = 2 if (self.flags % 10) == 0 else 4
        dtype = "<u2" if bytes_per_sample == 2 else "<u4"
        for start_sample, end_sample in zip(self.snippet_start_sample, self.snippet_end_sample):
            n = end_sample - start_sample + 1
            if n < 0:
                raise ValueError("Record 7028 has an invalid snippet sample range")
            byte_count = n * bytes_per_sample
            if offset + byte_count > len(data):
                raise ValueError("Record 7028 snippet samples exceed the payload length")
            samples = np.frombuffer(data[offset:offset + byte_count], dtype=dtype, count=n).copy()
            self.snippet_samples.append(samples)
            offset += byte_count
        self.parse_check = True


PARSERS = {
    ResonDatagrams.POSITION: Data1003,
    ResonDatagrams.ROLLPITCHHEAVE: Data1012,
    ResonDatagrams.HEADING: Data1013,
    ResonDatagrams.SONARSETTINGS: Data7000,
    ResonDatagrams.BEAMGEO: Data7004,
    ResonDatagrams.TVG: Data7010,
    ResonDatagrams.BEAMFORMEDDATA: Data7018,
    ResonDatagrams.RAWDETECTDATA: Data7027,
    ResonDatagrams.SNIPPETDATA: Data7028,
}


def parse(chunk: bytes, dg_type: ResonDatagrams) -> ResonData:
    parser = PARSERS.get(dg_type)
    if parser is None:
        raise NotImplementedError(f"Parser not implemented for S7K Record {dg_type.value}")
    return parser(chunk)
