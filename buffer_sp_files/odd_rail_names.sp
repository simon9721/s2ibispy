* odd_rail_names_realistic.sp
* Modified for realism: Multi-stage tapered buffer with parasitics, scaled sizes for IO-like drive.
* Tests supply name recognition with vpwr/vssd.
* Stage 1 (input inverter)
mx20 vpwr in n2 vpwr pfet w=3.6e-06 l=6e-07 ad=2.1015e-11 as=5.4e-12 pd=2.355e-05 ps=6.6e-06
mx11 vssd in n2 vssd nfet w=1.8e-06 l=6e-07 ad=1.107e-11 as=2.7e-12 pd=1.35e-05 ps=4.8e-06
* Stage 2
mx21 n3 n2 vpwr vpwr pfet w=1.41e-05 l=6e-07 ad=2.115e-11 as=2.1015e-11 pd=1.71e-05 ps=2.355e-05
mx12 n3 n2 vssd vssd nfet w=7.2e-06 l=6e-07 ad=1.08e-11 as=1.107e-11 pd=1.02e-05 ps=1.35e-05
* Stage 3 (parallel)
mx23 vpwr n3 n4 vpwr pfet w=3.21e-05 l=6e-07 ad=9.3915e-11 as=2.889e-11 pd=1.0125e-05 ps=1.8e-06
mx22 n4 n3 vpwr vpwr pfet w=3.21e-05 l=6e-07 ad=2.889e-11 as=4.815e-11 pd=1.8e-06 ps=3.51e-05
mx14 vssd n3 n4 vssd nfet w=1.62e-05 l=6e-07 ad=4.725e-11 as=1.458e-11 pd=7.575e-06 ps=1.8e-06
mx13 n4 n3 vssd vssd nfet w=1.62e-05 l=6e-07 ad=1.458e-11 as=2.43e-11 pd=1.8e-06 ps=1.92e-05
* Output stage (5x parallel, longer L for IO)
mx28 out n4 vpwr vpwr pfet w=4.215e-05 l=9e-07 ad=1.0116e-10 as=7.587e-11 pd=4.695e-05 ps=3.6e-06
mx27 vpwr n4 out vpwr pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mx26 out n4 vpwr vpwr pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mx25 vpwr n4 out vpwr pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=7.587e-11 pd=3.6e-06 ps=3.6e-06
mx24 out n4 vpwr vpwr pfet w=4.215e-05 l=9e-07 ad=7.587e-11 as=9.3915e-11 pd=3.6e-06 ps=1.0125e-05
mx19 out n4 vssd vssd nfet w=2.115e-05 l=9e-07 ad=5.076e-11 as=3.807e-11 pd=2.595e-05 ps=3.6e-06
mx18 vssd n4 out vssd nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mx17 out n4 vssd vssd nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mx16 vssd n4 out vssd nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mx15 out n4 vssd vssd nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=4.725e-11 pd=3.6e-06 ps=7.575e-06
* Parasitic capacitances (scaled/estimated from layout extraction)
cx10 n4 vssd 3.96825e-15
cx9 n4 vpwr 7.81995e-15
cx8 n4 out 9.1464e-15
cx7 n4 vssd 3.96825e-15
cx6 n4 vpwr 7.81995e-15
cx5 n4 out 9.1464e-15
cx4 n3 vssd 3.159e-15
cx3 n4 out 2.214e-15
cx2 n4 vssd 2.75184e-15
cx1 n3 vssd 3.46437e-15
cx0 n4 vssd 2.30877e-15
