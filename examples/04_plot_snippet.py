import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"

import matplotlib.pyplot as plt

from config import S7K_FILE, FIGURE_DIR
from reson7k import Reson, ResonDatagrams


with Reson(S7K_FILE) as reader:
    records = reader.get_datagram(ResonDatagrams.SNIPPETDATA, range(1))

if not records:
    raise SystemExit("No Record 7028 snippet data found.")

r = records[0]
if not r.snippet_samples:
    raise SystemExit("Record 7028 contains no snippet samples.")

# Choose the beam with the most samples in the first ping.
i = max(
    range(len(r.snippet_samples)),
    key=lambda index: len(r.snippet_samples[index]),
)

samples = r.snippet_samples[i]
start = r.snippet_start_sample[i]
bottom = r.bottom_detect_sample[i]
x = range(start, start + len(samples))

plt.figure(figsize=(9, 5))
plt.plot(x, samples)
plt.axvline(bottom, linestyle="--", label="Bottom detection")
plt.xlabel("Sample number")
plt.ylabel("Snippet amplitude (raw counts)")
plt.title(f"Record 7028 - Ping {r.ping_number}, Beam {r.beam_number[i]}")
plt.legend()
plt.tight_layout()

out = FIGURE_DIR / "snippet_example.png"
plt.savefig(out, dpi=180)
plt.show()

print(f"Saved: {out}")
print(
    f"Ping {r.ping_number}, beam {r.beam_number[i]}: "
    f"{len(samples)} samples, bounds "
    f"{start}..{r.snippet_end_sample[i]}"
)