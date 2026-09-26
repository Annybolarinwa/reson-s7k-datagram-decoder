import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
import pandas as pd
from config import S7K_FILE, OUTPUT_DIR
from reson7k import Reson, ResonDatagrams

rows = []
with Reson(S7K_FILE) as reader:
    records = reader.get_datagram(ResonDatagrams.SNIPPETDATA)

for r in records:
    for i, samples in enumerate(r.snippet_samples):
        rows.append({
            "ping_number": r.ping_number,
            "beam_number": r.beam_number[i],
            "start_sample": r.snippet_start_sample[i],
            "bottom_detect_sample": r.bottom_detect_sample[i],
            "end_sample": r.snippet_end_sample[i],
            "num_samples": len(samples),
            "max_amplitude": int(samples.max()) if len(samples) else None,
            "mean_amplitude": float(samples.mean()) if len(samples) else None,
        })

df = pd.DataFrame(rows)
out = OUTPUT_DIR / "snippet_summary.csv"
df.to_csv(out, index=False)
print(f"Exported {len(df):,} beam snippets to {out}")
