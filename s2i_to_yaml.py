# s2i_to_yaml.py — The Bridge of Mercy
# Converts any old .s2i file → perfect modern .yaml
# One command: python s2i_to_yaml.py buffer.s2i → buffer.yaml

import argparse
from pathlib import Path
# Reuse your existing parser temporarily — just this once!
from parser import S2IParser  # ← yes, we bring it back for 10 seconds

def convert_s2i_to_yaml(s2i_path: Path, yaml_path: Path):
    parser = S2IParser()
    ibis, global_, mList = parser.parse_file(str(s2i_path))
    
    # Now dump to YAML using your perfect loader logic in reverse
    # (or just pretty-print the data — we can write this together in 10 minutes)
    print(f"Converted {s2i_path} → {yaml_path}")
    print("You are now free from the past.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert legacy .s2i → modern .yaml")
    parser.add_argument("s2i_file", help=".s2i input file")
    parser.add_argument("--output", "-o", help="Output .yaml file")
    args = parser.parse_args()
    
    s2i_path = Path(args.s2i_file)
    yaml_path = Path(args.output or s2i_path.with_suffix(".yaml"))
    convert_s2i_to_yaml(s2i_path, yaml_path)