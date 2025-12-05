

****** PrimeSim HSPICE -- T-2022.06 win64 (May 20 2022 7637141) ******          

 Input File: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\correlate_

 lic:  

 lic: FLEXlm: SDK_12.10 

 lic: USER:   sh3qm                HOSTNAME: rd78ece-emclab 

 lic: HOSTID: 00ff89f5aa52         PID:      16448 

 lic: Using FLEXlm license file: 

 lic: 1704@synopsys.lic.mst.edu 

 lic: Checkout 1 hspice 

 lic: License/Maintenance for hspice will expire on 04-may-2026/2025.06 

 lic: 1(in_use)/50(total) FLOATING license(s) on SERVER 1704@synopsys.lic.mst.ed

 lic:   
Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\io_buf.ibs for IBIS 3.2 Compatibility...

WARNING (line   15) - Component 'MCM Driver 1' contains a blank character.
NOTE (line   61) - Pulldown Typical data is non-monotonic
NOTE (line   61) - Pulldown Maximum data is non-monotonic
NOTE (line   66) - Pulldown Minimum data is non-monotonic
NOTE (line  152) - Pullup Typical data is non-monotonic
NOTE (line  155) - Pullup Maximum data is non-monotonic
NOTE (line  226) - Pullup Minimum data is non-monotonic
NOTE (line  266) - GND Clamp Minimum data is non-monotonic
NOTE (line  276) - GND Clamp Typical data is non-monotonic
NOTE (line  277) - GND Clamp Maximum data is non-monotonic
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation


 init: begin read circuit files, cpu clock= 1.35E-01                            

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

Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\io_buf.ibs for IBIS 3.2 Compatibility...

WARNING (line   15) - Component 'MCM Driver 1' contains a blank character.
NOTE (line   61) - Pulldown Typical data is non-monotonic
NOTE (line   61) - Pulldown Maximum data is non-monotonic
NOTE (line   66) - Pulldown Minimum data is non-monotonic
NOTE (line  152) - Pullup Typical data is non-monotonic
NOTE (line  155) - Pullup Maximum data is non-monotonic
NOTE (line  226) - Pullup Minimum data is non-monotonic
NOTE (line  266) - GND Clamp Minimum data is non-monotonic
NOTE (line  276) - GND Clamp Typical data is non-monotonic
NOTE (line  277) - GND Clamp Maximum data is non-monotonic
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation

Errors  : 0
Warnings: 4

File Passed


 init: end read circuit files, cpu clock= 1.44E-01 peak memory=      71 mb      

 init: begin check errors, cpu clock= 1.44E-01                                  

 init: end check errors, cpu clock= 1.75E-01 peak memory=      72 mb            

 init: begin setup matrix, pivot=     0 cpu clock= 1.75E-01                     

       establish matrix -- done, cpu clock= 1.75E-01 peak memory=      72 mb    

       re-order matrix -- done, cpu clock= 1.76E-01 peak memory=      72 mb     

 init: end setup matrix, cpu clock= 1.77E-01 peak memory=      73 mb            

 dcop: begin dcop, cpu clock= 1.86E-01                                          

 dcop: end dcop, cpu clock= 1.92E-01 peak memory=      73 mb tot_iter=      39  

 output: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\correlate_driv

 sweep: tran tran0    begin, stop_t=  5.00E-08 #sweeps=**** cpu clock= 1.93E-01 

 tran: time= 5.1671E-09 tot_iter=     386 conv_iter=     142 cpu clock= 2.27E-01

 tran: time= 1.0038E-08 tot_iter=     746 conv_iter=     322 cpu clock= 2.50E-01

 tran: time= 1.5054E-08 tot_iter=     836 conv_iter=     367 cpu clock= 2.58E-01

 tran: time= 2.0188E-08 tot_iter=    1322 conv_iter=     546 cpu clock= 3.02E-01

 tran: time= 2.5035E-08 tot_iter=    1474 conv_iter=     622 cpu clock= 3.15E-01

 tran: time= 3.0136E-08 tot_iter=    1838 conv_iter=     760 cpu clock= 3.51E-01

 tran: time= 3.5001E-08 tot_iter=    2197 conv_iter=     910 cpu clock= 3.85E-01

 tran: time= 4.0055E-08 tot_iter=    2299 conv_iter=     961 cpu clock= 3.93E-01

 tran: time= 4.5010E-08 tot_iter=    2526 conv_iter=    1054 cpu clock= 4.14E-01

 tran: time= 5.0000E-08 tot_iter=    2647 conv_iter=    1113 cpu clock= 4.26E-01

 sweep: tran tran0    end, cpu clock= 4.26E-01 peak memory=      73 mb          

>info:         ***** hspice job concluded                                       

           total cpu time            0.33 seconds                               

           total elapsed time            0.43 seconds                           

           job started at     23:15:55 12/02/2025                               

           job ended   at     23:15:55 12/02/2025                               
>info:         ***** hspice job concluded


 lic: Release hspice token(s) 


****** PrimeSim HSPICE -- T-2022.06 win64 (May 20 2022 7637141) ******          

 Input File: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\correlate_

 lic:  

 lic: FLEXlm: SDK_12.10 

 lic: USER:   sh3qm                HOSTNAME: rd78ece-emclab 

 lic: HOSTID: 00ff89f5aa52         PID:      10096 

 lic: Using FLEXlm license file: 

 lic: 1704@synopsys.lic.mst.edu 

 lic: Checkout 1 hspice 

 lic: License/Maintenance for hspice will expire on 04-may-2026/2025.06 

 lic: 1(in_use)/50(total) FLOATING license(s) on SERVER 1704@synopsys.lic.mst.ed

 lic:   
Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\io_buf.ibs for IBIS 4.2 Compatibility...

WARNING (line   15) - Component 'MCM Driver 1' contains a blank character.
NOTE (line   61) - Pulldown Typical data is non-monotonic
NOTE (line   61) - Pulldown Maximum data is non-monotonic
NOTE (line   66) - Pulldown Minimum data is non-monotonic
NOTE (line  152) - Pullup Typical data is non-monotonic
NOTE (line  155) - Pullup Maximum data is non-monotonic
NOTE (line  226) - Pullup Minimum data is non-monotonic
NOTE (line  266) - GND Clamp Minimum data is non-monotonic
NOTE (line  276) - GND Clamp Typical data is non-monotonic
NOTE (line  277) - GND Clamp Maximum data is non-monotonic
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation


 init: begin read circuit files, cpu clock= 1.48E-01                            

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

Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\io_buf.ibs for IBIS 4.2 Compatibility...

WARNING (line   15) - Component 'MCM Driver 1' contains a blank character.
NOTE (line   61) - Pulldown Typical data is non-monotonic
NOTE (line   61) - Pulldown Maximum data is non-monotonic
NOTE (line   66) - Pulldown Minimum data is non-monotonic
NOTE (line  152) - Pullup Typical data is non-monotonic
NOTE (line  155) - Pullup Maximum data is non-monotonic
NOTE (line  226) - Pullup Minimum data is non-monotonic
NOTE (line  266) - GND Clamp Minimum data is non-monotonic
NOTE (line  276) - GND Clamp Typical data is non-monotonic
NOTE (line  277) - GND Clamp Maximum data is non-monotonic
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation

Errors  : 0
Warnings: 4

File Passed


 init: end read circuit files, cpu clock= 1.84E-01 peak memory=      72 mb      

 init: begin check errors, cpu clock= 1.84E-01                                  

 init: end check errors, cpu clock= 2.19E-01 peak memory=      73 mb            

 init: begin setup matrix, pivot=     0 cpu clock= 2.19E-01                     

       establish matrix -- done, cpu clock= 2.19E-01 peak memory=      73 mb    

       re-order matrix -- done, cpu clock= 2.19E-01 peak memory=      73 mb     

 init: end setup matrix, cpu clock= 2.21E-01 peak memory=      74 mb            

 dcop: begin dcop, cpu clock= 2.32E-01                                          

 dcop: end dcop, cpu clock= 2.37E-01 peak memory=      74 mb tot_iter=      39  

 output: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\correlate_driv

 sweep: tran tran0    begin, stop_t=  5.00E-08 #sweeps=**** cpu clock= 2.38E-01 

 tran: time= 5.1795E-09 tot_iter=     384 conv_iter=     145 cpu clock= 2.70E-01

 tran: time= 1.0018E-08 tot_iter=     658 conv_iter=     282 cpu clock= 2.88E-01

 tran: time= 1.5054E-08 tot_iter=     744 conv_iter=     325 cpu clock= 2.94E-01

 tran: time= 2.0049E-08 tot_iter=    1242 conv_iter=     509 cpu clock= 3.36E-01

 tran: time= 2.5031E-08 tot_iter=    1396 conv_iter=     586 cpu clock= 3.46E-01

 tran: time= 3.0118E-08 tot_iter=    1752 conv_iter=     723 cpu clock= 3.82E-01

 tran: time= 3.5061E-08 tot_iter=    2108 conv_iter=     873 cpu clock= 4.11E-01

 tran: time= 4.0055E-08 tot_iter=    2240 conv_iter=     939 cpu clock= 4.20E-01

 tran: time= 4.5204E-08 tot_iter=    2514 conv_iter=    1051 cpu clock= 4.50E-01

 tran: time= 5.0000E-08 tot_iter=    2637 conv_iter=    1108 cpu clock= 4.66E-01

 sweep: tran tran0    end, cpu clock= 4.66E-01 peak memory=      74 mb          

>info:         ***** hspice job concluded                                       

           total cpu time            0.37 seconds                               

           total elapsed time            0.47 seconds                           

           job started at     23:22:05 12/02/2025                               

           job ended   at     23:22:05 12/02/2025                               
>info:         ***** hspice job concluded


 lic: Release hspice token(s) 


****** PrimeSim HSPICE -- T-2022.06 win64 (May 20 2022 7637141) ******          

 Input File: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\correlate_

 lic:  

 lic: FLEXlm: SDK_12.10 

 lic: USER:   sh3qm                HOSTNAME: rd78ece-emclab 

 lic: HOSTID: 00ff89f5aa52         PID:      2484 

 lic: Using FLEXlm license file: 

 lic: 1704@synopsys.lic.mst.edu 

 lic: Checkout 1 hspice 

 lic: License/Maintenance for hspice will expire on 04-may-2026/2025.06 

 lic: 1(in_use)/50(total) FLOATING license(s) on SERVER 1704@synopsys.lic.mst.ed

 lic:   
Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\io_buf.ibs for IBIS 6.1 Compatibility...

WARNING (line   15) - Component 'MCM Driver 1' contains a blank character.
NOTE (line   61) - Pulldown Typical data is non-monotonic
NOTE (line   61) - Pulldown Maximum data is non-monotonic
NOTE (line   66) - Pulldown Minimum data is non-monotonic
NOTE (line  152) - Pullup Typical data is non-monotonic
NOTE (line  155) - Pullup Maximum data is non-monotonic
NOTE (line  226) - Pullup Minimum data is non-monotonic
NOTE (line  266) - GND Clamp Minimum data is non-monotonic
NOTE (line  276) - GND Clamp Typical data is non-monotonic
NOTE (line  277) - GND Clamp Maximum data is non-monotonic
NOTE (line  494) - ISSO_PU Maximum data is non-monotonic
NOTE (line  495) - ISSO_PU Typical data is non-monotonic
NOTE (line  495) - ISSO_PU Minimum data is non-monotonic
NOTE (line  539) - ISSO_PD Minimum data is non-monotonic
NOTE (line  542) - ISSO_PD Typical data is non-monotonic
NOTE (line  542) - ISSO_PD Maximum data is non-monotonic
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


 init: begin read circuit files, cpu clock= 1.68E-01                            

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

Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\io_buf.ibs for IBIS 6.1 Compatibility...

WARNING (line   15) - Component 'MCM Driver 1' contains a blank character.
NOTE (line   61) - Pulldown Typical data is non-monotonic
NOTE (line   61) - Pulldown Maximum data is non-monotonic
NOTE (line   66) - Pulldown Minimum data is non-monotonic
NOTE (line  152) - Pullup Typical data is non-monotonic
NOTE (line  155) - Pullup Maximum data is non-monotonic
NOTE (line  226) - Pullup Minimum data is non-monotonic
NOTE (line  266) - GND Clamp Minimum data is non-monotonic
NOTE (line  276) - GND Clamp Typical data is non-monotonic
NOTE (line  277) - GND Clamp Maximum data is non-monotonic
NOTE (line  494) - ISSO_PU Maximum data is non-monotonic
NOTE (line  495) - ISSO_PU Typical data is non-monotonic
NOTE (line  495) - ISSO_PU Minimum data is non-monotonic
NOTE (line  539) - ISSO_PD Minimum data is non-monotonic
NOTE (line  542) - ISSO_PD Typical data is non-monotonic
NOTE (line  542) - ISSO_PD Maximum data is non-monotonic
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


 init: end read circuit files, cpu clock= 2.14E-01 peak memory=      72 mb      

 init: begin check errors, cpu clock= 2.14E-01                                  

 init: end check errors, cpu clock= 2.38E-01 peak memory=      74 mb            

 init: begin setup matrix, pivot=     0 cpu clock= 2.38E-01                     

       establish matrix -- done, cpu clock= 2.38E-01 peak memory=      75 mb    

       re-order matrix -- done, cpu clock= 2.38E-01 peak memory=      75 mb     

 init: end setup matrix, cpu clock= 2.40E-01 peak memory=      75 mb            

 dcop: begin dcop, cpu clock= 2.55E-01                                          

 dcop: end dcop, cpu clock= 2.61E-01 peak memory=      75 mb tot_iter=      39  

 output: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\io_buf\correlate_driv

 sweep: tran tran0    begin, stop_t=  5.00E-08 #sweeps=**** cpu clock= 2.61E-01 

 tran: time= 5.3234E-09 tot_iter=     420 conv_iter=     166 cpu clock= 3.01E-01

 tran: time= 1.0012E-08 tot_iter=     744 conv_iter=     328 cpu clock= 3.23E-01

 tran: time= 1.5054E-08 tot_iter=     834 conv_iter=     373 cpu clock= 3.29E-01

 tran: time= 2.0133E-08 tot_iter=    1325 conv_iter=     554 cpu clock= 3.69E-01

 tran: time= 2.5018E-08 tot_iter=    1463 conv_iter=     623 cpu clock= 3.79E-01

 tran: time= 3.0102E-08 tot_iter=    1931 conv_iter=     814 cpu clock= 4.19E-01

 tran: time= 3.5028E-08 tot_iter=    2385 conv_iter=    1010 cpu clock= 4.55E-01

 tran: time= 4.0026E-08 tot_iter=    2541 conv_iter=    1088 cpu clock= 4.66E-01

 tran: time= 4.5235E-08 tot_iter=    2731 conv_iter=    1171 cpu clock= 4.83E-01

 tran: time= 5.0000E-08 tot_iter=    2914 conv_iter=    1259 cpu clock= 4.99E-01

 sweep: tran tran0    end, cpu clock= 4.99E-01 peak memory=      75 mb          

>info:         ***** hspice job concluded                                       

           total cpu time            0.40 seconds                               

           total elapsed time            0.50 seconds                           

           job started at     23:23:52 12/02/2025                               

           job ended   at     23:23:53 12/02/2025                               
>info:         ***** hspice job concluded


 lic: Release hspice token(s) 
