import re
from jinja2 import Template
import datetime
import os
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from tkinter import messagebox
import time

# Node name mapping for flexibility
NODE_MAPPING = {
    'input': 'in', 'sig_in': 'in', 'in': 'in', 'IN': 'in', 'din': 'in', 'sig': 'in', 'In': 'in',
    'output': 'out', 'sig_out': 'out', 'out': 'out', 'OUT': 'out', 'pad': 'out', 'PAD': 'out', 'PAD0': 'out', 'net7': 'out',
    'out_p': 'outp', 'out_n': 'outn',
    'vcc': 'vdd', 'vccq': 'vdd', 'VDD': 'vdd', 'vpwr': 'vdd',
    'gnd': 'vss', 'vssq': 'vss', 'VSS': 'vss', 'vssd': 'vss',
    'oe': 'enable', 'oe_b': 'enable_b', 'en_b': 'enable_b', 'en': 'enable', 'se': 'enable'
}

def parse_netlist(netlist_file, data, forced_model_type=None):
    if not os.path.exists(netlist_file):
        raise FileNotFoundError(f"Netlist file '{netlist_file}' not found")

    pins = []
    transistors = []
    nodes = set()
    gate_to_nodes = {}
    drain_to_nodes = {}
    node_sizes = {}

    with open(netlist_file, 'r') as f:
        lines = f.readlines()

    transistor_pattern = re.compile(r'^(m\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(pfet|nfet)\s+.*w=(\S+).*$', re.IGNORECASE)

    for line in lines:
        line = line.strip()
        if line.startswith('*') or not line:
            continue
        match = transistor_pattern.match(line)
        if match:
            name, drain, gate, source, bulk, t_type, width = match.groups()
            width_value = float(width.replace('u', '')) if 'u' in width else float(width)
            transistors.append((name, drain, gate, source, bulk, t_type.lower(), width_value))
            nodes.update([drain, gate, source, bulk])
            gate_to_nodes[gate] = gate_to_nodes.get(gate, set()).union({drain, source, bulk})
            drain_to_nodes[drain] = drain_to_nodes.get(drain, set()).union({gate, source, bulk})
            node_sizes[drain] = node_sizes.get(drain, 0) + width_value

    normalized_nodes = {node: NODE_MAPPING.get(node.lower(), node) for node in nodes}
    raw_nodes = {node: node for node in nodes}

    power_candidates = set()
    ground_candidates = set()
    input_candidates = {}  # {normalized: raw}
    enable_candidates = {}  # {normalized: raw}
    output_candidates = set()

    for t in transistors:
        _, drain, gate, source, bulk, t_type, _ = t
        normalized_source = normalized_nodes[source]
        normalized_bulk = normalized_nodes[bulk]
        if t_type == 'pfet' and source == bulk:
            power_candidates.add(normalized_source)
        elif t_type == 'nfet' and source == bulk:
            ground_candidates.add(normalized_source)

    driven_nodes = set(drain_to_nodes.keys())
    for gate, connected_nodes in gate_to_nodes.items():
        normalized_gate = normalized_nodes[gate]
        if normalized_gate in {'in', 'enable', 'enable_b', 'out'} and gate not in driven_nodes:
            input_candidates[normalized_gate] = gate
            if normalized_gate in {'enable', 'enable_b'}:
                enable_candidates[normalized_gate] = gate

    max_width = max(node_sizes.values(), default=0)
    output_candidates = {node for node, size in node_sizes.items() if size == max_width and (normalized_nodes[node] == 'out' or node.lower() in {'out_p', 'out_n'})}

    output_candidates = output_candidates or {node for node, size in node_sizes.items() if normalized_nodes[node] == 'out'}

    is_open_drain = not any(t[1] in output_candidates and t[5] == 'pfet' for t in transistors)

    diff_pin_candidates = {node for node in nodes if node.lower().startswith('out_') and node.lower() != 'out'}
    diff_pins = None
    if len(diff_pin_candidates) == 2:
        diff_pins = sorted([normalized_nodes[node] for node in diff_pin_candidates])

    series_pin_mapping = None
    for t in transistors:
        _, drain, _, source, _, t_type, _ = t
        normalized_drain = normalized_nodes[drain]
        normalized_source = normalized_nodes[source]
        if normalized_drain in output_candidates and normalized_source not in power_candidates | ground_candidates:
            series_pin_mapping = {'pin1': normalized_drain, 'pin2': normalized_source}
            break

    # Define models first to use model_type in pin population
    model_type = 'Output'  # Default for simple output
    bidir_nodes = {gate for gate in gate_to_nodes if gate in driven_nodes and normalized_nodes[gate] in {'out', 'outp', 'outn'}}
    if is_open_drain:
        model_type = 'Open_drain'
    elif series_pin_mapping:
        model_type = 'Series'
    elif diff_pins:
        model_type = 'Output_diff'
    elif bidir_nodes:
        model_type = 'I/O'
    elif enable_candidates:
        model_type = '3-State'
    elif not output_candidates:
        model_type = 'Input'

    if forced_model_type and forced_model_type in {'Output', 'I/O', '3-State', 'Open_drain', 'Series', 'Output_diff', 'Input'}:
        model_type = forced_model_type

    # Populate pins
    pin_data = []
    if diff_pins:
        raw_input = input_candidates.get('in')
        raw_enable = enable_candidates.get('enable') if 'enable' in enable_candidates else enable_candidates.get('enable_b')
        for pin in diff_pin_candidates:
            pin_data.append({
                'pin_name': normalized_nodes[pin],
                'spice_node': raw_nodes[pin],
                'signal_name': normalized_nodes[pin],
                'model': 'diff_model',
                'input_pin': raw_input,
                'enable_pin': raw_enable
            })
    elif series_pin_mapping:
        raw_enable = enable_candidates.get('enable') if 'enable' in enable_candidates else enable_candidates.get('enable_b')
        pin_data.extend([
            {'pin_name': series_pin_mapping['pin1'], 'spice_node': raw_nodes.get(series_pin_mapping['pin1'], series_pin_mapping['pin1']), 'signal_name': series_pin_mapping['pin1'], 'model': 'series_model', 'input_pin': None, 'enable_pin': raw_enable},
            {'pin_name': series_pin_mapping['pin2'], 'spice_node': raw_nodes.get(series_pin_mapping['pin2'], series_pin_mapping['pin2']), 'signal_name': series_pin_mapping['pin2'], 'model': 'series_model', 'input_pin': None, 'enable_pin': raw_enable}
        ])
    elif output_candidates:
        raw_input = input_candidates.get('in')
        raw_enable = enable_candidates.get('enable') if 'enable' in enable_candidates else enable_candidates.get('enable_b')
        for out_node in output_candidates:
            pin_data.append({
                'pin_name': normalized_nodes[out_node],
                'spice_node': raw_nodes[out_node],
                'signal_name': normalized_nodes[out_node],
                'model': 'driver' if not is_open_drain else 'open_drain_model',
                'input_pin': raw_input,
                'enable_pin': raw_enable
            })

    # For input_candidates, exclude bidirectional pins in I/O mode to avoid duplicate
    bidir_norm = {normalized_nodes[node] for node in bidir_nodes} if model_type == 'I/O' else set()
    for normalized, raw in input_candidates.items():
        if normalized not in {'enable', 'enable_b'} and normalized not in bidir_norm:
            model_name = 'input_model' if not output_candidates else 'dummy'
            pin_data.append({
                'pin_name': normalized,
                'spice_node': raw,
                'signal_name': normalized,
                'model': model_name,
                'input_pin': None,
                'enable_pin': None
            })

    power_nodes = power_candidates - set(input_candidates.keys()) - output_candidates
    ground_nodes = ground_candidates - set(input_candidates.keys()) - output_candidates
    for pwr in power_nodes:
        pin_data.append({
            'pin_name': pwr,
            'spice_node': raw_nodes.get(pwr, pwr),
            'signal_name': pwr,
            'model': 'POWER',
            'input_pin': None,
            'enable_pin': None
        })
    for gnd in ground_nodes:
        pin_data.append({
            'pin_name': gnd,
            'spice_node': raw_nodes.get(gnd, gnd),
            'signal_name': gnd,
            'model': 'GND',
            'input_pin': None,
            'enable_pin': None
        })

    # Define models
    models = []
    if output_candidates or diff_pins or series_pin_mapping:
        waveforms = (
            [{'rload': '50', 'vref': data['voltage_range']['typ']}] if is_open_drain
            else [{'rload': '50', 'vref': '0'}, {'rload': '50', 'vref': data['voltage_range']['typ']}]
        )
        models.append({
            'name': 'driver' if not is_open_drain else 'open_drain_model' if not diff_pins else 'diff_model' if not series_pin_mapping else 'series_model',
            'type': model_type,
            'file': {'typ': 'hspice.mod', 'min': 'hspice.mod', 'max': 'hspice.mod'},
            'enable': enable_candidates.get('enable') or enable_candidates.get('enable_b'),
            'polarity': 'Non-inverting' if not diff_pins else None,
            'rising_waveforms': waveforms,
            'falling_waveforms': waveforms
        })
    elif not output_candidates and 'in' in input_candidates:
        models.append({
            'name': 'input_model',
            'type': 'Input',
            'file': {'typ': 'hspice.mod', 'min': 'hspice.mod', 'max': 'hspice.mod'},
            'enable': None,
            'polarity': None
        })

    models.append({
        'name': 'dummy',
        'no_model': True,
        'type': 'Input'
    })

    return {
        'pins': pin_data,
        'models': models,
        'diff_pins': diff_pins,
        'series_pin_mapping': series_pin_mapping
    }

class T2BGui:
    # (same as previous, but with updated validate_unit)
    def validate_unit(self, value, name, unit):
        try:
            if unit == 'ohms':
                num_str = value.replace(' ohms', '').strip()
                num = float(num_str)
                if num <= 0:
                    self.log(f"Warning: {name} must be positive.", 'warning')
                    return False
                return True
            elif unit == 'ns':
                num_str = value.replace('ns', '').strip()
                num = float(num_str)
                if num <= 0:
                    self.log(f"Warning: {name} must be positive.", 'warning')
                    return False
                return True
            elif unit in ['m', 'nH', 'pF']:
                num = float(value.replace(unit, ''))
                if num <= 0:
                    self.log(f"Warning: {name} must be positive.", 'warning')
                    return False
                return True
            else:
                self.log(f"Warning: Invalid unit for {name}: expected {unit}.", 'warning')
                return False
        except ValueError:
            self.log(f"Warning: Invalid {name}: '{value}' is not valid with unit {unit}.", 'warning')
            return False

    # (rest of the class remains the same)

if __name__ == "__name__":
    root = tk.Tk()
    app = T2BGui(root)
    root.mainloop()