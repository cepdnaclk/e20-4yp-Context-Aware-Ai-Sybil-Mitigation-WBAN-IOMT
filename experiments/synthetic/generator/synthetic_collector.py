import csv
import random

random.seed(42)

# ------------------------------------------------------------
# OUTPUT FILES
# ------------------------------------------------------------
NORMAL_OUT = "normal_only_edgecase.csv"
SYBIL_OUT = "sybil_only_edgecase.csv"
MIXED_OUT = "mixed_edgecase.csv"

# ------------------------------------------------------------
# DATASET SETTINGS
# ------------------------------------------------------------
NUM_WINDOWS = 300000
WINDOW_DURATION = 5.0
WINDOW_STEP = 1.0

# ------------------------------------------------------------
# FIXED COLUMN ORDER
# ------------------------------------------------------------
COLUMNS = [
    "node_id",
    "node_mac",
    "window_start_s",
    "window_end_s",
    "pps",
    "iat_mean",
    "iat_std",
    "seq_gap_mean",
    "seq_gap_max",
    "seq_reset_rate",
    "dup_seq_rate",
    "out_of_order_rate",
    "boot_change_rate",
    "udp_pkt_count",
    "rssi_mean",
    "rssi_std",
    "rssi_min",
    "rssi_max",
    "rssi_frame_count",
    "rssi_missing",
    "label",
]

# ------------------------------------------------------------
# NODE PROFILES
# PPS unchanged
# ------------------------------------------------------------
LEGIT_NODES = [
    {
        "node_id": "ecg_01",
        "node_mac": "7c:9e:bd:f6:ce:40",
        "pps_mean": 10.0,
        "pps_std": 0.5,
        "rssi_mean": -41.0,
        "rssi_std": 1.5,
        "rssi_min": -45.0,
        "rssi_max": -35.0,
        "label": 0,
    },
    {
        "node_id": "eeg_01",
        "node_mac": "34:94:54:aa:79:d0",
        "pps_mean": 20.0,
        "pps_std": 0.8,
        "rssi_mean": -44.0,
        "rssi_std": 1.8,
        "rssi_min": -49.0,
        "rssi_max": -38.0,
        "label": 0,
    },
]

SYBIL_NODES = [
    {
        "node_id": "ecg_01_clone",
        "node_mac": "7c:9e:bd:f6:ce:48",
        "pps_mean": 50.0,
        "pps_std": 2.0,
        "rssi_mean": -40.2,   # only slightly shifted
        "rssi_std": 1.7,
        "rssi_min": -43.0,
        "rssi_max": -32.0,
        "label": 1,
    },
    {
        "node_id": "eeg_01_sybil",
        "node_mac": "34:94:54:aa:79:e0",
        "pps_mean": 100.0,
        "pps_std": 5.0,
        "rssi_mean": -60.5,   # less extreme than before
        "rssi_std": 2.0,
        "rssi_min": -66.0,
        "rssi_max": -56.0,
        "label": 1,
    },
]

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def make_row(
    node_id,
    node_mac,
    window_start_s,
    window_end_s,
    pps,
    iat_mean,
    iat_std,
    seq_gap_mean,
    seq_gap_max,
    seq_reset_rate,
    dup_seq_rate,
    out_of_order_rate,
    boot_change_rate,
    udp_pkt_count,
    rssi_mean,
    rssi_std,
    rssi_min,
    rssi_max,
    rssi_frame_count,
    rssi_missing,
    label,
):
    return {
        "node_id": node_id,
        "node_mac": node_mac,
        "window_start_s": f"{window_start_s:.6f}".rstrip("0").rstrip("."),
        "window_end_s": f"{window_end_s:.6f}".rstrip("0").rstrip("."),
        "pps": f"{pps:.1f}" if abs(pps - round(pps, 1)) < 1e-9 else f"{pps:.6f}",
        "iat_mean": f"{iat_mean:.9f}",
        "iat_std": f"{iat_std:.9f}",
        "seq_gap_mean": f"{seq_gap_mean:.9f}".rstrip("0").rstrip("."),
        "seq_gap_max": f"{seq_gap_max:.1f}",
        "seq_reset_rate": f"{seq_reset_rate:.1f}" if seq_reset_rate == 0 else f"{seq_reset_rate:.4f}",
        "dup_seq_rate": f"{dup_seq_rate:.1f}" if dup_seq_rate == 0 else f"{dup_seq_rate:.4f}",
        "out_of_order_rate": f"{out_of_order_rate:.1f}" if out_of_order_rate == 0 else f"{out_of_order_rate:.4f}",
        "boot_change_rate": f"{boot_change_rate:.1f}" if boot_change_rate == 0 else f"{boot_change_rate:.4f}",
        "udp_pkt_count": str(int(udp_pkt_count)),
        "rssi_mean": f"{rssi_mean:.8f}",
        "rssi_std": f"{rssi_std:.9f}",
        "rssi_min": f"{rssi_min:.1f}",
        "rssi_max": f"{rssi_max:.1f}",
        "rssi_frame_count": str(int(rssi_frame_count)),
        "rssi_missing": str(int(rssi_missing)),
        "label": str(int(label)),
    }


# ------------------------------------------------------------
# NORMAL GENERATOR
# ------------------------------------------------------------
def generate_normal_row(profile, t):
    pps = clamp(
        random.gauss(profile["pps_mean"], profile["pps_std"]),
        profile["pps_mean"] * 0.9,
        profile["pps_mean"] * 1.1,
    )
    udp_pkt_count = int(round(pps * WINDOW_DURATION))

    base_iat = 1.0 / pps
    iat_mean = max(0.0001, random.gauss(base_iat, base_iat * 0.01))
    iat_std = max(0.0003, random.gauss(base_iat * 0.08, base_iat * 0.02))

    seq_gap_mean = 1.0
    seq_gap_max = 1.0
    seq_reset_rate = 0.0
    dup_seq_rate = 0.0
    out_of_order_rate = 0.0
    boot_change_rate = 0.0

    rssi_mean = random.gauss(profile["rssi_mean"], 0.35)
    rssi_std = clamp(random.gauss(profile["rssi_std"], 0.18), 0.8, 2.5)
    rssi_min = profile["rssi_min"]
    rssi_max = profile["rssi_max"]

    rssi_frame_count = int(round(udp_pkt_count * random.uniform(0.95, 1.05)))
    rssi_missing = 0

    return make_row(
        profile["node_id"],
        profile["node_mac"],
        t,
        t + WINDOW_DURATION,
        pps,
        iat_mean,
        iat_std,
        seq_gap_mean,
        seq_gap_max,
        seq_reset_rate,
        dup_seq_rate,
        out_of_order_rate,
        boot_change_rate,
        udp_pkt_count,
        rssi_mean,
        rssi_std,
        rssi_min,
        rssi_max,
        rssi_frame_count,
        rssi_missing,
        profile["label"],
    )


# ------------------------------------------------------------
# EDGE-CASE SYBIL GENERATOR
# About 20% different in non-PPS behavior
# ------------------------------------------------------------
def generate_sybil_row(profile, t):
    pps = clamp(
        random.gauss(profile["pps_mean"], profile["pps_std"]),
        profile["pps_mean"] * 0.90,
        profile["pps_mean"] * 1.10,
    )
    udp_pkt_count = int(round(pps * WINDOW_DURATION))
    base_iat = 1.0 / pps

    if profile["node_id"] == "ecg_01_clone":
        # very close to clean behavior, only slightly different
        iat_mean = max(0.0001, random.gauss(base_iat * 1.03, base_iat * 0.012))
        iat_std = clamp(random.gauss(base_iat * 0.095, base_iat * 0.02), base_iat * 0.06, base_iat * 0.14)

        seq_gap_mean = clamp(random.gauss(1.015, 0.012), 1.0, 1.06)
        seq_gap_max = float(random.choice([1, 1, 1, 2]))
        seq_reset_rate = 0.0 if random.random() < 0.985 else round(random.uniform(0.002, 0.008), 4)
        dup_seq_rate = 0.0 if random.random() < 0.980 else round(random.uniform(0.002, 0.010), 4)
        out_of_order_rate = 0.0 if random.random() < 0.975 else round(random.uniform(0.003, 0.012), 4)
        boot_change_rate = 0.0 if random.random() < 0.990 else round(random.uniform(0.002, 0.006), 4)

        rssi_mean = random.gauss(profile["rssi_mean"], 0.12)
        rssi_std = clamp(random.gauss(profile["rssi_std"], 0.10), 1.1, 2.2)
        rssi_frame_count = int(round(udp_pkt_count * random.uniform(0.92, 1.00)))
        rssi_missing = 0 if random.random() < 0.985 else 1

    else:
        # EEG sybil also very close, but still slightly weaker and noisier
        iat_mean = max(0.0001, random.gauss(base_iat * 1.04, base_iat * 0.015))
        iat_std = clamp(random.gauss(base_iat * 0.11, base_iat * 0.025), base_iat * 0.07, base_iat * 0.17)

        seq_gap_mean = clamp(random.gauss(1.02, 0.018), 1.0, 1.08)
        seq_gap_max = float(random.choice([1, 1, 1, 2, 2, 3]))
        seq_reset_rate = 0.0 if random.random() < 0.980 else round(random.uniform(0.002, 0.010), 4)
        dup_seq_rate = 0.0 if random.random() < 0.975 else round(random.uniform(0.003, 0.012), 4)
        out_of_order_rate = 0.0 if random.random() < 0.970 else round(random.uniform(0.004, 0.015), 4)
        boot_change_rate = 0.0 if random.random() < 0.985 else round(random.uniform(0.002, 0.008), 4)

        rssi_mean = random.gauss(profile["rssi_mean"], 0.10)
        rssi_std = clamp(random.gauss(profile["rssi_std"], 0.10), 1.6, 2.5)
        rssi_frame_count = int(round(udp_pkt_count * random.uniform(0.80, 0.92)))
        rssi_missing = 0 if random.random() < 0.980 else random.randint(1, 2)

    rssi_min = profile["rssi_min"]
    rssi_max = profile["rssi_max"]

    return make_row(
        profile["node_id"],
        profile["node_mac"],
        t,
        t + WINDOW_DURATION,
        pps,
        iat_mean,
        iat_std,
        seq_gap_mean,
        seq_gap_max,
        seq_reset_rate,
        dup_seq_rate,
        out_of_order_rate,
        boot_change_rate,
        udp_pkt_count,
        rssi_mean,
        rssi_std,
        rssi_min,
        rssi_max,
        rssi_frame_count,
        rssi_missing,
        profile["label"],
    )


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    normal_rows = []
    sybil_rows = []
    mixed_rows = []

    start_t = 0.0

    for i in range(NUM_WINDOWS):
        t = start_t + i * WINDOW_STEP

        for profile in LEGIT_NODES:
            row = generate_normal_row(profile, t)
            normal_rows.append(row)
            mixed_rows.append(row)

        for profile in SYBIL_NODES:
            row = generate_sybil_row(profile, t)
            sybil_rows.append(row)
            mixed_rows.append(row)

    write_csv(NORMAL_OUT, normal_rows)
    write_csv(SYBIL_OUT, sybil_rows)
    write_csv(MIXED_OUT, mixed_rows)

    print(f"Generated {len(normal_rows)} rows -> {NORMAL_OUT}")
    print(f"Generated {len(sybil_rows)} rows -> {SYBIL_OUT}")
    print(f"Generated {len(mixed_rows)} rows -> {MIXED_OUT}")


if __name__ == "__main__":
    main()