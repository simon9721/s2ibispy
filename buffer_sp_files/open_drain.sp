* open_drain_realistic.sp
* Modified for realism: Multi-stage predriver for 'in', paralleled NMOS output for pull-down; dummy PMOS scaled small; parasitics added.
* Predriver stage 1
mx20 vdd in n2 vdd pfet w=3.6e-06 l=6e-07 ad=2.1015e-11 as=5.4e-12 pd=2.355e-05 ps=6.6e-06
mx11 vss in n2 vss nfet w=1.8e-06 l=6e-07 ad=1.107e-11 as=2.7e-12 pd=1.35e-05 ps=4.8e-06
* Stage 2
mx21 n3 n2 vdd vdd pfet w=1.41e-05 l=6e-07 ad=2.115e-11 as=2.1015e-11 pd=1.71e-05 ps=2.355e-05
mx12 n3 n2 vss vss nfet w=7.2e-06 l=6e-07 ad=1.08e-11 as=1.107e-11 pd=1.02e-05 ps=1.35e-05
* Stage 3 (focus on NMOS path)
mx14 vss n3 n4 vss nfet w=1.62e-05 l=6e-07 ad=4.725e-11 as=1.458e-11 pd=7.575e-06 ps=1.8e-06
mx13 n4 n3 vss vss nfet w=1.62e-05 l=6e-07 ad=1.458e-11 as=2.43e-11 pd=1.8e-06 ps=1.92e-05
* Dummy PMOS (small, for rail discovery)
mx23 vdd n3 n4 vdd pfet w=0.642e-05 l=6e-07 ad=1.8783e-11 as=5.778e-12 pd=2.025e-06 ps=0.36e-06
* Output NMOS (paralleled, longer L)
mx19 out n4 vss vss nfet w=2.115e-05 l=9e-07 ad=5.076e-11 as=3.807e-11 pd=2.595e-05 ps=3.6e-06
mx18 vss n4 out vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mx17 out n4 vss vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mx16 vss n4 out vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mx15 out n4 vss vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=4.725e-11 pd=3.6e-06 ps=7.575e-06
* Parasitics (focused on NMOS paths)
cx10 n4 vss 3.96825e-15
cx9 n4 vdd 7.81995e-15
cx8 n4 out 9.1464e-15
cx7 n4 vss 3.96825e-15
cx6 n4 vdd 7.81995e-15
cx5 n4 out 9.1464e-15
cx4 n3 vss 3.159e-15
cx3 n4 out 2.214e-15
cx2 n4 vss 2.75184e-15
cx1 n3 vss 3.46437e-15
cx0 n4 vss 2.30877e-15

