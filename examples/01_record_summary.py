from config import S7K_FILE
from reson7k import Reson

with Reson(S7K_FILE) as reader:
    summary = reader.record_summary()

print(f"File: {S7K_FILE.name}\n")
print("Record   Count")
print("------   -----")
for record, count in summary.items():
    print(f"{record:<8} {count}")
