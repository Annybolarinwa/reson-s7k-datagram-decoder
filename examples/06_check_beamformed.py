import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"

import numpy as np

from config import S7K_FILE
from reson7k import Reson, ResonDatagrams


with Reson(S7K_FILE) as reader:
    count = reader.record_summary().get(7018, 0)
    print(f"Record 7018 count: {count}")

    if count == 0:
        raise SystemExit("This file has no Record 7018 data.")

    record = reader.get_datagram(
        ResonDatagrams.BEAMFORMEDDATA,
        range(1),
    )[0]

print(f"Ping number: {record.ping_number}")
print(f"Number of beams: {record.num_beams}")
print(f"Number of samples: {record.num_samples}")
print(f"Amplitude array shape: {record.amplitude.shape}")
print(f"Phase array shape: {record.phase_raw.shape}")
print(f"Amplitude range: {record.amplitude.min()} to {record.amplitude.max()}")
print(f"Phase raw range: {record.phase_raw.min()} to {record.phase_raw.max()}")
print(f"Nonzero amplitude samples: {np.count_nonzero(record.amplitude):,}")