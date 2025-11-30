* input_only_realistic_with_esd.sp
* Enhanced two-stage input buffer with tapering, paralleled second stage, parasitics, and ESD diodes for clamp currents.
* Stage 1 (pad receiver)
mxp n1 in vdd vdd pfet w=3.6e-06 l=6e-07 ad=2.1015e-11 as=5.4e-12 pd=2.355e-05 ps=6.6e-06
mxn n1 in vss vss nfet w=1.8e-06 l=6e-07 ad=1.107e-11 as=2.7e-12 pd=1.35e-05 ps=4.8e-06
* Stage 2 (internal driver, paralleled for load)
mxp21 n2 n1 vdd vdd pfet w=1.41e-05 l=6e-07 ad=2.115e-11 as=2.1015e-11 pd=1.71e-05 ps=2.355e-05
mxp22 n2 n1 vdd vdd pfet w=1.41e-05 l=6e-07 ad=2.115e-11 as=2.1015e-11 pd=1.71e-05 ps=2.355e-05
mxn21 n2 n1 vss vss nfet w=7.2e-06 l=6e-07 ad=1.08e-11 as=1.107e-11 pd=1.02e-05 ps=1.35e-05
mxn22 n2 n1 vss vss nfet w=7.2e-06 l=6e-07 ad=1.08e-11 as=1.107e-11 pd=1.02e-05 ps=1.35e-05
* ESD protection diodes
d1 in vss gnd_diode
d2 in vdd pwr_diode
.model gnd_diode D IS=1e-15 RS=10 BV=5.5
.model pwr_diode D IS=1e-15 RS=10 BV=5.5
* Parasitics (focused on input/internal nodes)
cx10 n1 vss 3.96825e-15
cx9 n1 vdd 7.81995e-15
cx8 n1 n2 9.1464e-15
cx7 n2 vss 3.96825e-15
cx6 n2 vdd 7.81995e-15
cx5 n2 in 9.1464e-15
cx4 n1 vss 3.159e-15
cx3 n2 in 2.214e-15
cx2 n2 vss 2.75184e-15
cx1 n1 vss 3.46437e-15
cx0 n2 vss 2.30877e-15