* diff_driver_realistic.sp
* Modified for realism: Multi-stage for single-ended IN to differential OUT_P/OUT_N; paralleled outputs, parasitics; added tapering for in_b generation.
* Inverter chain for in to in_b
mxi20 vdd in n_i1 vdd pfet w=3.6e-06 l=6e-07 ad=2.1015e-11 as=5.4e-12 pd=2.355e-05 ps=6.6e-06
mxi11 vss in n_i1 vss nfet w=1.8e-06 l=6e-07 ad=1.107e-11 as=2.7e-12 pd=1.35e-05 ps=4.8e-06
mxi21 in_b n_i1 vdd vdd pfet w=1.41e-05 l=6e-07 ad=2.115e-11 as=2.1015e-11 pd=1.71e-05 ps=2.355e-05
mxi12 in_b n_i1 vss vss nfet w=7.2e-06 l=6e-07 ad=1.08e-11 as=1.107e-11 pd=1.02e-05 ps=1.35e-05
* Driver for OUT_P (tapered)
mxp20 vdd in n_p2 vdd pfet w=3.6e-06 l=6e-07 ad=2.1015e-11 as=5.4e-12 pd=2.355e-05 ps=6.6e-06
mxn11 vss in n_p2 vss nfet w=1.8e-06 l=6e-07 ad=1.107e-11 as=2.7e-12 pd=1.35e-05 ps=4.8e-06
mxp21 n_p3 n_p2 vdd vdd pfet w=1.41e-05 l=6e-07 ad=2.115e-11 as=2.1015e-11 pd=1.71e-05 ps=2.355e-05
mxn12 n_p3 n_p2 vss vss nfet w=7.2e-06 l=6e-07 ad=1.08e-11 as=1.107e-11 pd=1.02e-05 ps=1.35e-05
mxp23 vdd n_p3 n_p4 vdd pfet w=3.21e-05 l=6e-07 ad=9.3915e-11 as=2.889e-11 pd=1.0125e-05 ps=1.8e-06
mxp22 n_p4 n_p3 vdd vdd pfet w=3.21e-05 l=6e-07 ad=2.889e-11 as=4.815e-11 pd=1.8e-06 ps=3.51e-05
mxn14 vss n_p3 n_p4 vss nfet w=1.62e-05 l=6e-07 ad=4.725e-11 as=1.458e-11 pd=7.575e-06 ps=1.8e-06
mxn13 n_p4 n_p3 vss vss nfet w=1.62e-05 l=6e-07 ad=1.458e-11 as=2.43e-11 pd=1.8e-06 ps=1.92e-05
* OUT_P output
mxp28 out_p n_p4 vdd vdd pfet w=4.215e-05 l=9e-07 ad=1.0116e-10 as=7.587e-11 pd=4.695e-05 ps=3.6e-06
mxp27 vdd n_p4 out_p vdd pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mxp26 out_p n_p4 vdd vdd pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mxp25 vdd n_p4 out_p vdd pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mxp24 out_p n_p4 vdd vdd pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=9.3915e-11 pd=3.6e-06 ps=1.0125e-05
mxn19 out_p n_p4 vss vss nfet w=2.115e-05 l=9e-07 ad=5.076e-11 as=3.807e-11 pd=2.595e-05 ps=3.6e-06
mxn18 vss n_p4 out_p vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mxn17 out_p n_p4 vss vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mxn16 vss n_p4 out_p vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mxn15 out_p n_p4 vss vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=4.725e-11 pd=3.6e-06 ps=7.575e-06
* Driver for OUT_N (mirrored, driven by in_b)
mxp20n vdd in_b n_n2 vdd pfet w=3.6e-06 l=6e-07 ad=2.1015e-11 as=5.4e-12 pd=2.355e-05 ps=6.6e-06
mxn11n vss in_b n_n2 vss nfet w=1.8e-06 l=6e-07 ad=1.107e-11 as=2.7e-12 pd=1.35e-05 ps=4.8e-06
mxp21n n_n3 n_n2 vdd vdd pfet w=1.41e-05 l=6e-07 ad=2.115e-11 as=2.1015e-11 pd=1.71e-05 ps=2.355e-05
mxn12n n_n3 n_n2 vss vss nfet w=7.2e-06 l=6e-07 ad=1.08e-11 as=1.107e-11 pd=1.02e-05 ps=1.35e-05
mxp23n vdd n_n3 n_n4 vdd pfet w=3.21e-05 l=6e-07 ad=9.3915e-11 as=2.889e-11 pd=1.0125e-05 ps=1.8e-06
mxp22n n_n4 n_n3 vdd vdd pfet w=3.21e-05 l=6e-07 ad=2.889e-11 as=4.815e-11 pd=1.8e-06 ps=3.51e-05
mxn14n vss n_n3 n_n4 vss nfet w=1.62e-05 l=6e-07 ad=4.725e-11 as=1.458e-11 pd=7.575e-06 ps=1.8e-06
mxn13n n_n4 n_n3 vss vss nfet w=1.62e-05 l=6e-07 ad=1.458e-11 as=2.43e-11 pd=1.8e-06 ps=1.92e-05
* OUT_N output
mxp28n out_n n_n4 vdd vdd pfet w=4.215e-05 l=9e-07 ad=1.0116e-10 as=7.587e-11 pd=4.695e-05 ps=3.6e-06
mxp27n vdd n_n4 out_n vdd pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mxp26n out_n n_n4 vdd vdd pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mxp25n vdd n_n4 out_n vdd pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mxp24n out_n n_n4 vdd vdd pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=9.3915e-11 pd=3.6e-06 ps=1.0125e-05
mxn19n out_n n_n4 vss vss nfet w=2.115e-05 l=9e-07 ad=5.076e-11 as=3.807e-11 pd=2.595e-05 ps=3.6e-06
mxn18n vss n_n4 out_n vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mxn17n out_n n_n4 vss vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mxn16n vss n_n4 out_n vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mxn15n out_n n_n4 vss vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=4.725e-11 pd=3.6e-06 ps=7.575e-06
* Parasitics (duplicated for P/N paths)
cx10p n_p4 vss 3.96825e-15
cx9p n_p4 vdd 7.81995e-15
cx8p n_p4 out_p 9.1464e-15
cx7p n_p4 vss 3.96825e-15
cx6p n_p4 vdd 7.81995e-15
cx5p n_p4 out_p 9.1464e-15
cx4p n_p3 vss 3.159e-15
cx3p n_p4 out_p 2.214e-15
cx2p n_p4 vss 2.75184e-15
cx1p n_p3 vss 3.46437e-15
cx0p n_p4 vss 2.30877e-15
cx10n n_n4 vss 3.96825e-15
cx9n n_n4 vdd 7.81995e-15
cx8n n_n4 out_n 9.1464e-15
cx7n n_n4 vss 3.96825e-15
cx6n n_n4 vdd 7.81995e-15
cx5n n_n4 out_n 9.1464e-15
cx4n n_n3 vss 3.159e-15
cx3n n_n4 out_n 2.214e-15
cx2n n_n4 vss 2.75184e-15
cx1n n_n3 vss 3.46437e-15
cx0n n_n4 vss 2.30877e-15