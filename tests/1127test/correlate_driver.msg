

****** PrimeSim HSPICE -- T-2022.06 win64 (May 20 2022 7637141) ******          

 Input File: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\1127test\correlat

 lic:  

 lic: FLEXlm: SDK_12.10 

 lic: USER:   sh3qm                HOSTNAME: rd78ece-emclab 

 lic: HOSTID: 00ff89f5aa52         PID:      17856 

 lic: Using FLEXlm license file: 

 lic: 1704@synopsys.lic.mst.edu 

 lic: Checkout 1 hspice 

 lic: License/Maintenance for hspice will expire on 04-may-2026/2025.06 

 lic: 1(in_use)/50(total) FLOATING license(s) on SERVER 1704@synopsys.lic.mst.ed

 lic:   
Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\1127test\test.ibs for IBIS 6.0 Compatibility...

WARNING (line   20) - Component 'MCM Driver 1' contains a blank character.
NOTE (line   70) - Pulldown Typical data is non-monotonic
NOTE (line   70) - Pulldown Maximum data is non-monotonic
NOTE (line   75) - Pulldown Minimum data is non-monotonic
NOTE (line  161) - Pullup Typical data is non-monotonic
NOTE (line  164) - Pullup Maximum data is non-monotonic
NOTE (line  235) - Pullup Minimum data is non-monotonic
NOTE (line  275) - GND Clamp Minimum data is non-monotonic
NOTE (line  285) - GND Clamp Typical data is non-monotonic
NOTE (line  286) - GND Clamp Maximum data is non-monotonic
NOTE (line  503) - ISSO_PU Maximum data is non-monotonic
NOTE (line  504) - ISSO_PU Typical data is non-monotonic
NOTE (line  504) - ISSO_PU Minimum data is non-monotonic
NOTE (line  548) - ISSO_PD Minimum data is non-monotonic
NOTE (line  551) - ISSO_PD Typical data is non-monotonic
NOTE (line  551) - ISSO_PD Maximum data is non-monotonic
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
WARNING - Model driver: Typical ISSO_PU current (-1.008e-08A) at 0V is not within  5.00% of Pullup current (-3.628e-02A) at reference ( 0.000V)
WARNING - Model driver: Typical ISSO_PU current (-3.628e-02A) at Pulldown reference ( 0.000V) - table value ( 3.300V) is non-zero (> 1.0e-06A)
WARNING - Model driver: Minimum ISSO_PU current (-3.726e-08A) at 0V is not within  5.00% of Pullup current (-2.755e-02A) at reference ( 0.000V)
WARNING - Model driver: Minimum ISSO_PU current (-3.569e-02A) at Pulldown reference ( 0.000V) - table value ( 3.000V) is non-zero (> 1.0e-06A)
WARNING - Model driver: Maximum ISSO_PU current (-5.774e-09A) at 0V is not within  5.00% of Pullup current (-4.413e-02A) at reference ( 0.000V)
WARNING - Model driver: Maximum ISSO_PU current (-3.769e-02A) at Pulldown reference ( 0.000V) - table value ( 3.600V) is non-zero (> 1.0e-06A)


 init: begin read circuit files, cpu clock= 1.39E-01                            

       option search = C:/synopsys/Hspice_T-2022.06/parts/behave/               

       option search = C:/synopsys/Hspice_T-2022.06/parts/AD/                   

       option search = C:/synopsys/Hspice_T-2022.06/parts/XILINX/               

       option search = C:/synopsys/Hspice_T-2022.06/parts/TLINE/                

       option search = C:/synopsys/Hspice_T-2022.06/parts/TI/                   

       option search = C:/synopsys/Hspice_T-2022.06/parts/SIGNET/               

       option search = C:/synopsys/Hspice_T-2022.06/parts/PCI/                  

       option search = C:/synopsys/Hspice_T-2022.06/parts/LIN_TECH/             

       option search = C:/synopsys/Hspice_T-2022.06/parts/PET/                  

       option search = C:/synopsys/Hspice_T-2022.06/parts/DI0/                  

       option search = C:/synopsys/Hspice_T-2022.06/parts/COMLINE/              

       option search = C:/synopsys/Hspice_T-2022.06/parts/BURR_BRM/             

       option search = C:/synopsys/Hspice_T-2022.06/parts/BJT/                  

       option probe                                                             

       option accurate                                                          

       option rmax =    0.500                                                   

       option post_version =    9.601E+03                                       

       option post =     2.00                                                   
IBISCHK7 V7.1.0

Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\1127test\test.ibs for IBIS 6.0 Compatibility...

WARNING (line   20) - Component 'MCM Driver 1' contains a blank character.
NOTE (line   70) - Pulldown Typical data is non-monotonic
NOTE (line   70) - Pulldown Maximum data is non-monotonic
NOTE (line   75) - Pulldown Minimum data is non-monotonic
NOTE (line  161) - Pullup Typical data is non-monotonic
NOTE (line  164) - Pullup Maximum data is non-monotonic
NOTE (line  235) - Pullup Minimum data is non-monotonic
NOTE (line  275) - GND Clamp Minimum data is non-monotonic
NOTE (line  285) - GND Clamp Typical data is non-monotonic
NOTE (line  286) - GND Clamp Maximum data is non-monotonic
NOTE (line  503) - ISSO_PU Maximum data is non-monotonic
NOTE (line  504) - ISSO_PU Typical data is non-monotonic
NOTE (line  504) - ISSO_PU Minimum data is non-monotonic
NOTE (line  548) - ISSO_PD Minimum data is non-monotonic
NOTE (line  551) - ISSO_PD Typical data is non-monotonic
NOTE (line  551) - ISSO_PD Maximum data is non-monotonic
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
WARNING - Model driver: Typical ISSO_PU current (-1.008e-08A) at 0V is not within  5.00% of Pullup current (-3.628e-02A) at reference ( 0.000V)
WARNING - Model driver: Typical ISSO_PU current (-3.628e-02A) at Pulldown reference ( 0.000V) - table value ( 3.300V) is non-zero (> 1.0e-06A)
WARNING - Model driver: Minimum ISSO_PU current (-3.726e-08A) at 0V is not within  5.00% of Pullup current (-2.755e-02A) at reference ( 0.000V)
WARNING - Model driver: Minimum ISSO_PU current (-3.569e-02A) at Pulldown reference ( 0.000V) - table value ( 3.000V) is non-zero (> 1.0e-06A)
WARNING - Model driver: Maximum ISSO_PU current (-5.774e-09A) at 0V is not within  5.00% of Pullup current (-4.413e-02A) at reference ( 0.000V)
WARNING - Model driver: Maximum ISSO_PU current (-3.769e-02A) at Pulldown reference ( 0.000V) - table value ( 3.600V) is non-zero (> 1.0e-06A)

Errors  : 0
Warnings: 16

File Passed


 init: end read circuit files, cpu clock= 1.51E-01 peak memory=      71 mb      

 init: begin check errors, cpu clock= 1.51E-01                                  

 init: end check errors, cpu clock= 1.72E-01 peak memory=      72 mb            

 init: begin setup matrix, pivot=     0 cpu clock= 1.72E-01                     

       establish matrix -- done, cpu clock= 1.72E-01 peak memory=      72 mb    

       re-order matrix -- done, cpu clock= 1.73E-01 peak memory=      72 mb     

 init: end setup matrix, cpu clock= 1.74E-01 peak memory=      73 mb            

 dcop: begin dcop, cpu clock= 1.85E-01                                          

 dcop: end dcop, cpu clock= 1.91E-01 peak memory=      73 mb tot_iter=      39  

 output: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\1127test\correlate_dr

 sweep: tran tran0    begin, stop_t=  5.00E-08 #sweeps=**** cpu clock= 1.93E-01 

 tran: time= 5.0360E-09 tot_iter=     368 conv_iter=     133 cpu clock= 2.26E-01

 tran: time= 1.0044E-08 tot_iter=     662 conv_iter=     280 cpu clock= 2.45E-01

 tran: time= 1.5054E-08 tot_iter=     720 conv_iter=     309 cpu clock= 2.49E-01

 tran: time= 2.0136E-08 tot_iter=    1193 conv_iter=     479 cpu clock= 2.89E-01

 tran: time= 2.5101E-08 tot_iter=    1353 conv_iter=     559 cpu clock= 2.99E-01

 tran: time= 3.0032E-08 tot_iter=    1737 conv_iter=     705 cpu clock= 3.32E-01

 tran: time= 3.5066E-08 tot_iter=    2101 conv_iter=     865 cpu clock= 3.61E-01

 tran: time= 4.0018E-08 tot_iter=    2225 conv_iter=     927 cpu clock= 3.70E-01

 tran: time= 4.5228E-08 tot_iter=    2451 conv_iter=    1020 cpu clock= 3.88E-01

 tran: time= 5.0000E-08 tot_iter=    2605 conv_iter=    1092 cpu clock= 4.02E-01

 sweep: tran tran0    end, cpu clock= 4.02E-01 peak memory=      73 mb          

>info:         ***** hspice job concluded                                       

           total cpu time            0.30 seconds                               

           total elapsed time            0.40 seconds                           

           job started at     21:54:42 11/27/2025                               

           job ended   at     21:54:42 11/27/2025                               
>info:         ***** hspice job concluded


 lic: Release hspice token(s) 
