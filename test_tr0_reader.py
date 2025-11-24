# test_tr0_reader.py
import numpy as np
import matplotlib.pyplot as plt
import re

def parse_tr0_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Keep only lines that look like pure numeric data (11-char fields)
    data_lines = []
    for line in lines:
        s = line.strip()
        # Skip obvious footer / header lines
        if not s or s.startswith('$') or 'END' in s.upper() or 'Copyright' in s:
            continue
        # Keep only lines where every 11 chars is a valid scientific number
        if len(s) % 11 == 0:
            # Quick validity check on first field
            if re.match(r'[-+]?[0-9]*\.?[0-9]+[EeDd]?[-+]?[0-9]+', s[:11]):
                data_lines.append(s)

    if not data_lines:
        raise ValueError("No valid data found in the file!")

    # Concatenate all clean lines
    data_str = ''.join(data_lines)

    # Final sanity check
    value_length = 11
    if len(data_str) % value_length != 0:
        # Trim trailing garbage if any
        data_str = data_str[:len(data_str) // value_length * value_length]

    values = []
    for i in range(0, len(data_str), value_length):
        field = data_str[i:i+value_length].replace('D', 'E')  # HSPICE sometimes uses D
        try:
            values.append(float(field))
        except ValueError:
            print(f"Warning: Could not parse field: '{field}' → skipping rest")
            break

    values = np.array(values)
    if len(values) % 15 != 0:
        # Trim incomplete last row
        values = values[:len(values) // 15 * 15]

    data = values.reshape(-1, 15)

    # Remove the huge 1e31 end marker that HSPICE sometimes adds
    data = data[data[:, 0] < 1e20]

    print(f"Successfully loaded {len(data)} time points")
    return data


def plot_tr0_data(data):
    time_ns = data[:, 0] * 1e9  # show in nanoseconds

    labels = [
        "Input (SPICE)", "Input (IBIS)",
        "Driver Out1 (SPICE)", "Driver Out1 (IBIS)",
        "Driver Out2 (SPICE)", "Driver Out2 (IBIS)",
        "Driver Out3 (SPICE)", "Driver Out3 (IBIS)",
        "Far End1 (SPICE)", "Far End1 (IBIS)",
        "Far End2 (SPICE)", "Far End2 (IBIS)",
        "Far End3 (SPICE)", "Far End3 (IBIS)"
    ]

    pairs = [
        (1, 2, "Input"),
        (3, 4, "Driver Output 1"),
        (5, 6, "Driver Output 2"),
        (7, 8, "Driver Output 3"),
        (9, 10, "Far-End Line 1"),
        (11, 12, "Far-End Line 2"),
        (13, 14, "Far-End Line 3"),
    ]

    fig, axs = plt.subplots(7, 1, figsize=(12, 20), sharex=True)
    fig.suptitle("HSPICE vs IBIS Comparison", fontsize=16)

    for ax, (i1, i2, title) in zip(axs, pairs):
        ax.plot(time_ns, data[:, i1], label=labels[i1-1], linewidth=1.2)
        ax.plot(time_ns, data[:, i2], '--', label=labels[i2-1], linewidth=1.2)
        ax.set_ylabel("Voltage (V)")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

    axs[-1].set_xlabel("Time (ns)")
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.show()


if __name__ == "__main__":
    import os
    filename = "compare_driver.tr0"

    if not os.path.exists(filename):
        filename = input("Enter path to .tr0 file: ").strip('"')

    data = parse_tr0_file(filename)
    plot_tr0_data(data)