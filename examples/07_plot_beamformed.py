import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"

import numpy as np
import matplotlib.pyplot as plt

from config import S7K_FILE, FIGURE_DIR
from reson7k import Reson, ResonDatagrams


with Reson(S7K_FILE) as reader:
    records = reader.get_datagram(
        ResonDatagrams.BEAMFORMEDDATA,
        range(1),
    )

if not records:
    raise SystemExit("No Record 7018 beamformed data found.")

r = records[0]

# Log scaling makes weaker amplitudes visible alongside stronger returns.
image = np.log1p(r.amplitude.astype(np.float32))

fig, ax = plt.subplots(figsize=(11, 7))
plot = ax.imshow(
    image,
    aspect="auto",
    origin="upper",
    cmap="viridis",
    interpolation="nearest",
)
ax.set_xlabel("Beam number")
ax.set_ylabel("Sample number")
ax.set_title(f"Record 7018 amplitude preview — ping {r.ping_number}")
fig.colorbar(plot, ax=ax, label="log(1 + raw amplitude)")
fig.tight_layout()

out = FIGURE_DIR / "beamformed_amplitude.png"
fig.savefig(out, dpi=180)
plt.show()

print(f"Saved: {out}")
print(f"Array shape: {r.amplitude.shape}")