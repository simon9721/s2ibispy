Compare IBIS model with HSPICE model
**********************************************************************
.TRAN 5.0ps 100.0ns
.OPTIONS POST=1 POST_VERSION=9007 PROBE ACCURATE RMAX=0.5
.TEMP=50
.INCLUDE '..\Lab_1\IO_buf.inc'
.LIB     '..\Lab_1\Process.lib'  Typ
**********************************************************************
.PROBE TRAN Pls_SPICE   = V(Pls_SPICE)
+           Pls_IBIS    = V(Pls_IBIS)
+           out1SPICE   = V(out1SPICE)
+           out2SPICE   = V(out2SPICE)
+           out3SPICE   = V(out3SPICE)
+           out1IBIS    = V(out1IBIS)
+           out2IBIS    = V(out2IBIS)
+           out3IBIS    = V(out3IBIS)
+           end1SPICE   = V(end1SPICE)
+           end2SPICE   = V(end2SPICE)
+           end3SPICE   = V(end3SPICE)
+           end1IBIS    = V(end1IBIS)
+           end2IBIS    = V(end2IBIS)
+           end3IBIS    = V(end3IBIS)
**********************************************************************
Vpls_SPCIE  Pls_SPICE  0 PULSE (5.0V 0.0V 0.1ns 1.0ps 1.0ps 25.0ns 50.0ns)
Vpls_IBIS   Pls_IBIS   0 PULSE (5.0V 0.0V 0.1ns 1.0ps 1.0ps 25.0ns 50.0ns)
*
Vvcc Vcc   0 DC=5.0
Vgnd GRND  0 DC=0.0
**********************************************************************
X1SPICE  Pls_SPICE  out1SPICE  Vcc  Vcc  0  0  0  IO_buf
X2SPICE  GRND       out2SPICE  Vcc  Vcc  0  0  0  IO_buf
X3SPICE  Pls_SPICE  out3SPICE  Vcc  Vcc  0  0  0  IO_buf
*--------------------------------------------------------------------*
W_SPICE N=3  out1SPICE  out2SPICE  out3SPICE  0
+            end1SPICE  end2SPICE  end3SPICE  0
+ RLGCfile=Z50_406.lc3 l=1.2          $  50 Ohms
*+ RLGCfile=wel4rs.rlc l=1.2           $ 340 Ohms
**********************************************************************
B1IBIS   Vcc1bio GND1bio out1IBIS  Pls_IBIS  Vcc rcv1bio Vcc1cl_bio GND1cl_bio
+ file=  'lab_1.ibs'
+ model= 'io50v'
+ buffer= 3
+ ramp_rwf=2
+ ramp_fwf=2
+ power=on
R1bio  rcv1bio  0    R=1.0k
*
B2IBIS   Vcc2bio GND2bio out2IBIS  GRND      Vcc rcv2bio Vcc2cl_bio GND2cl_bio
+ file=  'lab_1.ibs'
+ model= 'io50v'
+ buffer= 3
+ ramp_rwf=2
+ ramp_fwf=2
+ power=on
R2bio  rcv2bio  0    R=1.0k
*
B3IBIS   Vcc3bio GND3bio out3IBIS  Pls_IBIS  Vcc rcv3bio Vcc3cl_bio GND3cl_bio
+ file=  'lab_1.ibs'
+ model= 'io50v'
+ buffer= 3
+ ramp_rwf=2
+ ramp_fwf=2
+ power=on
R3bio  rcv3bio  0    R=1.0k
*--------------------------------------------------------------------*
W_IBIS  N=3  out1IBIS   out2IBIS   out3IBIS   0
+            end1IBIS   end2IBIS   end3IBIS   0
+ RLGCfile=Z50_406.lc3 l=1.2          $  50 Ohms
*+ RLGCfile=wel4rs.rlc l=1.2           $ 340 Ohms
**********************************************************************
.END
***********************************************************************
