* series_element_realistic.sp
* Modified for realism: Added multi-stage for core_out driver, paralleled series switch (mxsw), parasitics; PAD external, CORE_OUT internal.
* Predriver for din to core_out
mx20 vdd din n2 vdd pfet w=3.6e-06 l=6e-07 ad=2.1015e-11 as=5.4e-12 pd=2.355e-05 ps=6.6e-06
mx11 vss din n2 vss nfet w=1.8e-06 l=6e-07 ad=1.107e-11 as=2.7e-12 pd=1.35e-05 ps=4.8e-06
mx21 core_out n2 vdd vdd pfet w=1.41e-05 l=6e-07 ad=2.115e-11 as=2.1015e-11 pd=1.71e-05 ps=2.355e-05
mx12 core_out n2 vss vss nfet w=7.2e-06 l=6e-07 ad=1.08e-11 as=1.107e-11 pd=1.02e-05 ps=1.35e-05
* Series switch (paralleled for strength, controlled by se)
mxsw1 pad se core_out vss nfet w=2.115e-05 l=9e-07 ad=5.076e-11 as=3.807e-11 pd=2.595e-05 ps=3.6e-06
mxsw2 pad se core_out vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mxsw3 pad se core_out vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mxsw4 pad se core_out vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=3.807e-11 pd=3.6e-06 ps=3.6e-06
mxsw5 pad se core_out vss nfet w=2.115e-05 l=9e-07 ad=3.807e-11 as=4.725e-11 pd=3.6e-06 ps=7.575e-06
* Parasitics (on core_out and pad)
cx10 core_out vss 3.96825e-15
cx9 core_out vdd 7.81995e-15
cx8 core_out pad 9.1464e-15
cx7 pad vss 3.96825e-15
cx6 pad vdd 7.81995e-15
cx5 pad core_out 9.1464e-15
cx4 n2 vss 3.159e-15
cx3 core_out pad 2.214e-15
cx2 pad vss 2.75184e-15
cx1 n2 vss 3.46437e-15
cx0 pad vss 2.30877e-15
