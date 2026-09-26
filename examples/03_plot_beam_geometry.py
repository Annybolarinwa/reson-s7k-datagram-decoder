import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"

import numpy as np
import matplotlib.pyplot as plt

from config import S7K_FILE, FIGURE_DIR
from reson7k import Reson, ResonDatagrams


with Reson(S7K_FILE) as reader:
    records = reader.get_datagram(ResonDatagrams.BEAMGEO, range(1))

if not records:
    raise SystemExit("No Record 7004 beam geometry found.")

r = records[0]
vertical_deg = np.degrees(r.rx_angle_vertical)
horizontal_deg = np.degrees(r.rx_angle_horizontal)

plt.figure(figsize=(9, 5))
plt.plot(
    r.rx_beam_number,
    horizontal_deg,
    label="Horizontal receive angle",
)

if not np.allclose(vertical_deg, vertical_deg[0]):
    plt.plot(
        r.rx_beam_number,
        vertical_deg,
        label="Vertical receive angle",
    )

plt.xlabel("Receive beam number")
plt.ylabel("Receive angle (degrees)")
plt.title("RESON S7K Record 7004 - Beam Geometry")
plt.grid(True, alpha=0.25)
plt.legend()
plt.tight_layout()

out = FIGURE_DIR / "beam_geometry.png"
plt.savefig(out, dpi=180)
plt.show()

print(f"Saved: {out}")
print(
    f"Horizontal angle range: "
    f"{horizontal_deg.min():.2f} to {horizontal_deg.max():.2f} degrees"
)
print(
    f"Vertical angle range: "
    f"{vertical_deg.min():.2f} to {vertical_deg.max():.2f} degrees"
)