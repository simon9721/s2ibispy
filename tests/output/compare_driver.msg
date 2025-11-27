

****** PrimeSim HSPICE -- T-2022.06 win64 (May 20 2022 7637141) ******          

 Input File: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\output\compare_dr

 lic:  

 lic: FLEXlm: SDK_12.10 

 lic: USER:   sh3qm                HOSTNAME: rd78ece-emclab 

 lic: HOSTID: 00ff89f5aa52         PID:      6024 

 lic: Using FLEXlm license file: 

 lic: 1704@synopsys.lic.mst.edu 

 lic: Checkout 1 hspice 

 lic: License/Maintenance for hspice will expire on 04-may-2026/2025.06 

 lic: 1(in_use)/50(total) FLOATING license(s) on SERVER 1704@synopsys.lic.mst.ed

 lic:   
Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\output\test.ibs for IBIS 3.2 Compatibility...

ERROR (line   15) - Exceeds 80 chararacters.
WARNING (line   23) - Component 'MCM Driver 1' contains a blank character.
ERROR (line   47) - Invalid Vinl Line
ERROR (line   48) - Invalid Vinh Line
NOTE (line   76) - Pulldown Typical data is non-monotonic
NOTE (line   76) - Pulldown Maximum data is non-monotonic
NOTE (line   81) - Pulldown Minimum data is non-monotonic
NOTE (line  167) - Pullup Typical data is non-monotonic
NOTE (line  170) - Pullup Maximum data is non-monotonic
NOTE (line  241) - Pullup Minimum data is non-monotonic
NOTE (line  281) - GND Clamp Minimum data is non-monotonic
NOTE (line  291) - GND Clamp Typical data is non-monotonic
NOTE (line  292) - GND Clamp Maximum data is non-monotonic
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation


 init: begin read circuit files, cpu clock= 1.46E-01                            

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

Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\output\test.ibs for IBIS 3.2 Compatibility...

ERROR (line   15) - Exceeds 80 chararacters.
WARNING (line   23) - Component 'MCM Driver 1' contains a blank character.
ERROR (line   47) - Invalid Vinl Line
ERROR (line   48) - Invalid Vinh Line
NOTE (line   76) - Pulldown Typical data is non-monotonic
NOTE (line   76) - Pulldown Maximum data is non-monotonic
NOTE (line   81) - Pulldown Minimum data is non-monotonic
NOTE (line  167) - Pullup Typical data is non-monotonic
NOTE (line  170) - Pullup Maximum data is non-monotonic
NOTE (line  241) - Pullup Minimum data is non-monotonic
NOTE (line  281) - GND Clamp Minimum data is non-monotonic
NOTE (line  291) - GND Clamp Typical data is non-monotonic
NOTE (line  292) - GND Clamp Maximum data is non-monotonic
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation

Errors  : 6
Warnings: 4

File Failed


 init: end read circuit files, cpu clock= 1.59E-01 peak memory=      71 mb      

 init: begin check errors, cpu clock= 1.59E-01                                  

 init: end check errors, cpu clock= 2.06E-01 peak memory=      72 mb            

 init: begin setup matrix, pivot=     0 cpu clock= 2.06E-01                     

       establish matrix -- done, cpu clock= 2.06E-01 peak memory=      72 mb    

       re-order matrix -- done, cpu clock= 2.07E-01 peak memory=      72 mb     

 init: end setup matrix, cpu clock= 2.09E-01 peak memory=      73 mb            

 dcop: begin dcop, cpu clock= 2.19E-01                                          

 dcop: end dcop, cpu clock= 2.26E-01 peak memory=      73 mb tot_iter=      39  

 output: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\output\compare_driver

 sweep: tran tran0    begin, stop_t=  5.00E-08 #sweeps=**** cpu clock= 2.27E-01 

 tran: time= 5.0360E-09 tot_iter=     368 conv_iter=     133 cpu clock= 2.62E-01

 tran: time= 1.0020E-08 tot_iter=     670 conv_iter=     284 cpu clock= 2.84E-01

 tran: time= 1.5054E-08 tot_iter=     726 conv_iter=     312 cpu clock= 2.88E-01

 tran: time= 2.0145E-08 tot_iter=    1160 conv_iter=     467 cpu clock= 3.28E-01

 tran: time= 2.5101E-08 tot_iter=    1310 conv_iter=     542 cpu clock= 3.38E-01

 tran: time= 3.0048E-08 tot_iter=    1694 conv_iter=     685 cpu clock= 3.75E-01

 tran: time= 3.5019E-08 tot_iter=    2068 conv_iter=     853 cpu clock= 4.09E-01

 tran: time= 4.0027E-08 tot_iter=    2210 conv_iter=     924 cpu clock= 4.19E-01

 tran: time= 4.5212E-08 tot_iter=    2388 conv_iter=    1001 cpu clock= 4.36E-01

 tran: time= 5.0000E-08 tot_iter=    2502 conv_iter=    1056 cpu clock= 4.47E-01

 sweep: tran tran0    end, cpu clock= 4.47E-01 peak memory=      73 mb          

>info:         ***** hspice job concluded                                       

           total cpu time            0.35 seconds                               

           total elapsed time            0.45 seconds                           

           job started at     12:33:14 11/26/2025                               

           job ended   at     12:33:14 11/26/2025                               
>info:         ***** hspice job concluded


 lic: Release hspice token(s) 


****** PrimeSim HSPICE -- T-2022.06 win64 (May 20 2022 7637141) ******          

 Input File: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\output\compare_dr

 lic:  

 lic: FLEXlm: SDK_12.10 

 lic: USER:   sh3qm                HOSTNAME: rd78ece-emclab 

 lic: HOSTID: 00ff89f5aa52         PID:      20896 

 lic: Using FLEXlm license file: 

 lic: 1704@synopsys.lic.mst.edu 

 lic: Checkout 1 hspice 

 lic: License/Maintenance for hspice will expire on 04-may-2026/2025.06 

 lic: 1(in_use)/50(total) FLOATING license(s) on SERVER 1704@synopsys.lic.mst.ed

 lic:   
Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\output\test.ibs for IBIS 3.2 Compatibility...

ERROR (line   15) - Exceeds 80 chararacters.
WARNING (line   23) - Component 'MCM Driver 1' contains a blank character.
ERROR (line   47) - Invalid Vinl Line
ERROR (line   48) - Invalid Vinh Line
NOTE (line   76) - Pulldown Typical data is non-monotonic
NOTE (line   76) - Pulldown Maximum data is non-monotonic
NOTE (line   81) - Pulldown Minimum data is non-monotonic
NOTE (line  167) - Pullup Typical data is non-monotonic
NOTE (line  170) - Pullup Maximum data is non-monotonic
NOTE (line  241) - Pullup Minimum data is non-monotonic
NOTE (line  281) - GND Clamp Minimum data is non-monotonic
NOTE (line  291) - GND Clamp Typical data is non-monotonic
NOTE (line  292) - GND Clamp Maximum data is non-monotonic
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

Checking C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\output\test.ibs for IBIS 3.2 Compatibility...

ERROR (line   15) - Exceeds 80 chararacters.
WARNING (line   23) - Component 'MCM Driver 1' contains a blank character.
ERROR (line   47) - Invalid Vinl Line
ERROR (line   48) - Invalid Vinh Line
NOTE (line   76) - Pulldown Typical data is non-monotonic
NOTE (line   76) - Pulldown Maximum data is non-monotonic
NOTE (line   81) - Pulldown Minimum data is non-monotonic
NOTE (line  167) - Pullup Typical data is non-monotonic
NOTE (line  170) - Pullup Maximum data is non-monotonic
NOTE (line  241) - Pullup Minimum data is non-monotonic
NOTE (line  281) - GND Clamp Minimum data is non-monotonic
NOTE (line  291) - GND Clamp Typical data is non-monotonic
NOTE (line  292) - GND Clamp Maximum data is non-monotonic
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation

Errors  : 6
Warnings: 4

File Failed


 init: end read circuit files, cpu clock= 1.59E-01 peak memory=      71 mb      

 init: begin check errors, cpu clock= 1.59E-01                                  

 init: end check errors, cpu clock= 2.06E-01 peak memory=      72 mb            

 init: begin setup matrix, pivot=     0 cpu clock= 2.06E-01                     

       establish matrix -- done, cpu clock= 2.07E-01 peak memory=      72 mb    

       re-order matrix -- done, cpu clock= 2.07E-01 peak memory=      72 mb     

 init: end setup matrix, cpu clock= 2.09E-01 peak memory=      73 mb            

 dcop: begin dcop, cpu clock= 2.21E-01                                          

 dcop: end dcop, cpu clock= 2.27E-01 peak memory=      73 mb tot_iter=      39  

 output: C:\Users\sh3qm\PycharmProjects\s2ibispy_new\tests\output\compare_driver

 sweep: tran tran0    begin, stop_t=  5.00E-08 #sweeps=**** cpu clock= 2.31E-01 

 tran: time= 5.0360E-09 tot_iter=     368 conv_iter=     133 cpu clock= 2.65E-01

 tran: time= 1.0020E-08 tot_iter=     670 conv_iter=     284 cpu clock= 2.86E-01

 tran: time= 1.5054E-08 tot_iter=     726 conv_iter=     312 cpu clock= 2.90E-01

 tran: time= 2.0145E-08 tot_iter=    1160 conv_iter=     467 cpu clock= 3.29E-01

 tran: time= 2.5101E-08 tot_iter=    1310 conv_iter=     542 cpu clock= 3.39E-01

 tran: time= 3.0048E-08 tot_iter=    1694 conv_iter=     685 cpu clock= 3.72E-01

 tran: time= 3.5019E-08 tot_iter=    2068 conv_iter=     853 cpu clock= 4.04E-01

 tran: time= 4.0027E-08 tot_iter=    2210 conv_iter=     924 cpu clock= 4.15E-01

 tran: time= 4.5212E-08 tot_iter=    2388 conv_iter=    1001 cpu clock= 4.31E-01

 tran: time= 5.0000E-08 tot_iter=    2502 conv_iter=    1056 cpu clock= 4.42E-01

 sweep: tran tran0    end, cpu clock= 4.43E-01 peak memory=      73 mb          

>info:         ***** hspice job concluded                                       

           total cpu time            0.35 seconds                               

           total elapsed time            0.44 seconds                           

           job started at     12:07:59 11/27/2025                               

           job ended   at     12:07:59 11/27/2025                               
>info:         ***** hspice job concluded


 lic: Release hspice token(s) 
