* optimized_tristate_output_v11.sp
* Optimized for Cadence T2B SPICE to IBIS conversion: Corrected AND implementation as NAND + inverter to avoid contention and Vth drop.
* Maintains tri-state success and improves falling test by ensuring full n3 swing.

* Predriver for IN (inverter to n1 = ~IN)
mx1 n1 in vdd vdd pfet w=3.6e-06 l=6e-07
mx2 n1 in vss vss nfet w=1.8e-06 l=6e-07

* Inverter for OE to oe_b = ~OE
mxi1 oe_b oe vdd vdd pfet w=0.6e-06 l=6e-07
mxi2 oe_b oe vss vss nfet w=0.3e-06 l=6e-07

* NAND for pullup gate n2 = ~(OE & IN)
mx5 n2 oe vdd vdd pfet w=3.21e-05 l=6e-07
mx5p n2 oe vdd vdd pfet w=3.21e-05 l=6e-07
mx6 n2 in vdd vdd pfet w=3.21e-05 l=6e-07
mx6p n2 in vdd vdd pfet w=3.21e-05 l=6e-07
mx7 n2 oe n_int1 vss nfet w=7.2e-06 l=6e-07
mx8 n_int1 in vss vss nfet w=7.2e-06 l=6e-07

* NAND for pulldown pre-gate nand_n3 = ~(OE & n1) = ~(OE & ~IN)
mx9 nand_n3 oe vdd vdd pfet w=3.21e-05 l=6e-07
mx9p nand_n3 oe vdd vdd pfet w=3.21e-05 l=6e-07
mx10 nand_n3 n1 vdd vdd pfet w=3.21e-05 l=6e-07
mx10p nand_n3 n1 vdd vdd pfet w=3.21e-05 l=6e-07
mx11 nand_n3 oe n_int2 vss nfet w=7.2e-06 l=6e-07
mx12 n_int2 n1 vss vss nfet w=7.2e-06 l=6e-07

* Inverter for n3 = ~ nand_n3 = OE & ~IN
mx13 n3 nand_n3 vdd vdd pfet w=3.21e-05 l=6e-07
mx14 n3 nand_n3 vss vss nfet w=7.2e-06 l=6e-07

* Output stage
mx28 out n2 vdd vdd pfet w=4.215e-05 l=9e-07
mx27 vdd n2 out vdd pfet w=4.215e-05 l=9e-07
mx26 out n2 vdd vdd pfet w=4.215e-05 l=9e-07
mx25 vdd n2 out vdd pfet w=4.215e-05 l=9e-07
mx24 out n2 vdd vdd pfet w=4.215e-05 l=9e-07
mx19 out n3 vss vss nfet w=2.115e-05 l=9e-07
mx18 vss n3 out vss nfet w=2.115e-05 l=9e-07
mx17 out n3 vss vss nfet w=2.115e-05 l=9e-07
mx16 vss n3 out vss nfet w=2.115e-05 l=9e-07
mx15 out n3 vss vss nfet w=2.115e-05 l=9e-07

* Parasitics - kept original realistic values
cx10 n2 vss 3.96825e-15
cx9 n2 vdd 7.81995e-15
cx8 n2 out 9.1464e-15
cx7 n3 vss 3.96825e-15
cx6 n3 vdd 7.81995e-15
cx5 n3 out 9.1464e-15
cx4 n1 vss 3.159e-15
cx3 n2 out 2.214e-15
cx2 n3 vss 2.75184e-15
cx1 n1 vss 3.46437e-15
cx0 n3 vss 2.30877e-15
cx_int1 n_int1 vss 1e-15
cx_int2 n_int2 vdd 1e-15