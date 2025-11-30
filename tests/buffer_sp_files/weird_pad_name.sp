* weird_pad_name_realistic.sp
* Modified for realism: Multi-stage tapered buffer with parasitics; PAD0 output, In input, VDD/VSS rails.
* Stage 1
mx20 VDD In n2 VDD pfet w=3.6e-06 l=6e-07 ad=2.1015e-11 as=5.4e-12 pd=2.355e-05 ps=6.6e-06
mx11 VSS In n2 VSS nfet w=1.8e-06 l=6e-07 ad=1.107e-11 as=2.7e-12 pd=1.35e-05 ps=4.8e-06
* Stage 2
mx21 n3 n2 VDD VDD pfet w=1.41e-05 l=6e-07 ad=2.115e-11 as=2.1015e-11 pd=1.71e-05 ps=2.355e-05
mx12 n3 n2 VSS VSS nfet w=7.2e-06 l=6e-07 ad=1.08e-11 as=1.107e-11 pd=1.02e-05 ps=1.35e-05
* Stage 3
mx23 VDD n3 n4 VDD pfet w=3.21e-05 l=6e-07 ad=9.3915e-11 as=2.889e-11 pd=1.0125e-05 ps=1.8e-06
mx22 n4 n3 VDD VDD pfet w=3.21e-05 l=6e-07 ad=2.889e-11 as=4.815e-11 pd=1.8e-06 ps=3.51e-05
mx14 VSS n3 n4 VSS nfet w=1.62e-05 l=6e-07 ad=4.725e-11 as=1.458e-11 pd=7.575e-06 ps=1.8e-06
mx13 n4 n3 VSS VSS nfet w=1.62e-05 l=6e-07 ad=1.458e-11 as=2.43e-11 pd=1.8e-06 ps=1.92e-05
* Output stage
mx28 PAD0 n4 VDD VDD pfet w=4.215e-05 l=9e-07 ad=1.0116e-10 as=7.587e-11 pd=4.695e-05 ps=3.6e-06
mx27 VDD n4 PAD0 VDD pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mx26 PAD0 n4 VDD VDD pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mx25 VDD n4 PAD0 VDD pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mx24 PAD0 n4 VDD VDD pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=9.3915e-11 pd=3.6e-06 ps=1.0125e-05
mx19 PAD0 n4 VSS VSS nfet w=2.115e-05 l=9e-07 ad=5.076e-11 as=3.807e-11 pd=2.595e-05 ps=3.6e-06
mx18 VSS n4 PAD0 VSS nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mx17 PAD0 n4 VSS VSS nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mx16 VSS n4 PAD0 VSS nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mx15 PAD0 n4 VSS VSS nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=4.725e-11 pd=3.6e-06 ps=7.575e-06
* Parasitics
cx10 n4 VSS 3.96825e-15
cx9 n4 VDD 7.81995e-15
cx8 n4 PAD0 9.1464e-15
cx7 n4 VSS 3.96825e-15
cx6 n4 VDD 7.81995e-15
cx5 n4 PAD0 9.1464e-15
cx4 n3 VSS 3.159e-15
cx3 n4 PAD0 2.214e-15
cx2 n4 VSS 2.75184e-15
cx1 n3 VSS 3.46437e-15
cx0 n4 VSS 2.30877e-15