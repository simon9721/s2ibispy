* test_io_buf_real_behavior.sp
* This deck will show you the TRUE behavior of your buffer
.TEMP 50
.OPTION POST ACCURATE

* Power
Vvdd vdd 0 DC 3.3
Vvss vss 0 DC 0

* Include your exact buffer — unchanged
.INCLUDE "io_buf.sp"
.INCLUDE "hspice.mod"

* === FOUR CORNERS TEST ===
* We drive IN and OE independently with clean pulses

* IN: 0 → 3.3V at 20ns, back to 0 at 60ns
Vin  in  0 PULSE(0 3.3 20n 1p 1p 20n 80n)

* OE: stays HIGH the whole time (enabled)
Voe  oe  0 DC 3.3

* Load (50Ω to ground — standard)
Rload out 0 50

* Probe everything important
.TRAN 0.1p 150n
.PROBE V(in) V(oe) V(out) V(n1) V(oe_b) V(n2) V(n3) V(nand_n3)

.END