S2IBIS3 DOCUMENTATION STRUCTURE

This directory contains the s2ibis3 reference documentation split into 
logical sections for easier navigation:

01_introduction.txt
    - Overview of s2ibis3
    - How to run s2ibis3 on Unix and Windows
    - Command language structure
    - Reserved words

02_header_commands.txt
    - Global header commands
    - IBIS version, file metadata
    - Spice configuration
    - Temperature and voltage ranges
    - Package parasitics
    - Simulation parameters
    - Derating specifications

03_component_description.txt
    - Component overview
    - [Component] keyword
    - Component header commands
    - Manufacturer and package info
    - Spice file references

04_pin_lists.txt
    - Differential pin list
    - Pin mapping
    - Pin list formats and specifications
    - Series pin mapping
    - Series switch groups

05_model_specification.txt
    - Model keyword and attributes
    - Model types (Input, Output, I/O, etc.)
    - Polarity and enable settings
    - Threshold voltages
    - Terminator parameters
    - Waveform specifications
    - Model file references

06_series_switch_models.txt
    - Series switch model parameters
    - [On] and [Off] states
    - Series MOSFET specifications
    - [R Series] parameters
    - BIRD 72.3 notes

For the complete original documentation, refer to s2ibis3.txt

North Carolina State University
IBIS v3.2 compatible
