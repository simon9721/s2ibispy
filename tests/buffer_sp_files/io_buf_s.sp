**********************************************************************
*  Bidirectional I/O Buffer – Hierarchical subcircuit for SPICE-to-IBIS
*  Based on your optimized_io_buffer_v11.sp
*  Fully compatible with Cadence IBIS generation flow
**********************************************************************

.SUBCKT IO_BUF  in oe out in_sense vdd vss  
* Pins: in = data input, oe = output enable, out = pad, in_sense = input receiver output
*       vdd/vss = power/ground (can be connected to power/g_clamp etc externally)

*=== Pre-driver: invert input =====================================
XINV_IN   in     n1     vdd vss  INVERTER_SMALL

*=== Pre-driver: invert OE =========================================
XINV_OE   oe     oe_b   vdd vss  INVERTER_SMALL

*=== Big NAND2 for pull-up control:  n2 = ~(in & oe) ===============
XNAND_PU  in  oe  n2  vdd vss  NAND2_BIG

*=== Big NAND2 + INV for pull-down control: n3 = ~(n1 & oe) ========
*     (equivalent to oe & ~in)
XNAND_PD1 oe  n1   nand_n3  vdd vss  NAND2_BIG
XINV_PD   nand_n3  n3   vdd vss  INVERTER_BIG

*=== Final output stage – multi-finger big transistors =============
* Pull-up: total W = 5 × 42.15 µm = 210.75 µm → use M=100 with base 2.1075 µm
Mp_big  out  n2  vdd  vdd  pfet  L=0.9e-6  W=42.15e-6  M=5   $ 5 fingers exactly as in original

* Pull-down: total W = 5 × 21.15 µm = 105.75 µm
Mn_big  out  n3  vss  vss  nfet  L=0.9e-6  W=21.15e-6  M=5   $ 5 fingers

*=== Weak input receiver from pad (required for IBIS input model) ==
XRCV      out    in_sense   vdd vss   INVERTER_TINY

*=== Parasitic capacitances (kept from your extraction) ============
cx10  n2   vss   3.96825e-15
cx9   n2   vdd   7.81995e-15
cx8   n2   out   9.1464e-15
cx7   n3   vss   3.96825e-15
cx6   n3   vdd   7.81995e-15
cx5   n3   out   9.1464e-15
cx4   n1   vss   3.159e-15
cx3   n2   out   2.214e-15
cx_int1 n_int1 vss 1e-15   $ if you ever bring these nodes out
cx_sense in_sense vss 1e-15

.ENDS IO_BUF
**********************************************************************

*====================================================================
* Small pre-driver inverter (used for in → n1 and oe → oe_b )
*====================================================================
.SUBCKT INVERTER_SMALL A Y vdd vss
Mp  Y A vdd vdd  pfet W=3.6e-6  L=0.6e-6
Mn  Y A vss vss  nfet W=1.8e-6  L=0.6e-6
.ENDS

*====================================================================
* Big NAND2 used for both pull-up and pull-down predrivers
*====================================================================
.SUBCKT NAND2_BIG A B Y vdd vss
* Two parallel PMOS for each input (exactly as in your netlist: mx5+mx5p etc)
Mp1 Y A vdd vdd pfet W=32.1e-6 L=0.6e-6
Mp2 Y A vdd vdd pfet W=32.1e-6 L=0.6e-6
Mp3 Y B vdd vdd pfet W=32.1e-6 L=0.6e-6
Mp4 Y B vdd vdd pfet W=32.1e-6 L=0.6e-6
* Series NMOS pair
Mn1 int_n B vss vss nfet W=7.2e-6 L=0.6e-6
Mn2 Y    A int_n vss nfet W=7.2e-6 L=0.6e-6
.ENDS

*====================================================================
* Big inverter for final pull-down control stage
*====================================================================
.SUBCKT INVERTER_BIG A Y vdd vss
Mp  Y A vdd vdd pfet W=32.1e-6 L=0.6e-6   $ strong pull-up
Mn  Y A vss vss nfet W=7.2e-6  L=0.6e-6   $ weaker pull-down is fine
.ENDS

*====================================================================
* Very weak pad → in_sense inverter (critical for IBIS input model)
*====================================================================
.SUBCKT INVERTER_TINY A Y vdd vss
Mp  Y A vdd vdd pfet W=0.6e-6 L=0.6e-6
Mn  Y A vss vss nfet W=0.3e-6 L=0.6e-6
.ENDS
**********************************************************************