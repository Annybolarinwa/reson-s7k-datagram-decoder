from config import S7K_FILE
from reson7k import Reson, ResonDatagrams

with Reson(S7K_FILE) as reader:
    records = reader.get_datagram(ResonDatagrams.SONARSETTINGS, range(1))

if not records:
    raise SystemExit("No Record 7000 sonar settings found.")

r = records[0]
print(f"Ping number:       {r.ping_number}")
print(f"Frequency:         {r.frequency:.2f} Hz")
print(f"Sample rate:       {r.sample_rate:.2f} Hz")
print(f"Transmit waveform: {r.tx_wave_form}")
print(f"Selected range:    {r.range_select:.2f} m")
print(f"Sound velocity:    {r.sound_velocity:.2f} m/s")
