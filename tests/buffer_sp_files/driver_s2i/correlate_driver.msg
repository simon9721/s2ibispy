

****** PrimeSim HSPICE -- T-2022.06 win64 (May 20 2022 7637141) ******          

 Input File: C:\Users\sh3qm\PycharmProjects\s2ibispy\tests\buffer_sp_files\drive

 lic:  

 lic: FLEXlm: SDK_12.10 

 lic: USER:   sh3qm                HOSTNAME: rd78ece-emclab 

 lic: HOSTID: 00ff89f5aa52         PID:      15468 

 lic: Using FLEXlm license file: 

 lic: 1704@synopsys.lic.mst.edu 

 lic: Checkout 1 hspice 

 lic: License/Maintenance for hspice will expire on 04-may-2026/2025.06 

 lic: 1(in_use)/50(total) FLOATING license(s) on SERVER 1704@synopsys.lic.mst.ed

 lic:   
Checking C:\Users\sh3qm\PycharmProjects\s2ibispy\tests\buffer_sp_files\driver_s2i\buffer.ibs for IBIS 7.1 Compatibility...

NOTE (line   60) - Pulldown Typical data is non-monotonic
NOTE (line   60) - Pulldown Maximum data is non-monotonic
NOTE (line   65) - Pulldown Minimum data is non-monotonic
NOTE (line  151) - Pullup Typical data is non-monotonic
NOTE (line  154) - Pullup Maximum data is non-monotonic
NOTE (line  225) - Pullup Minimum data is non-monotonic
NOTE (line  265) - GND Clamp Minimum data is non-monotonic
NOTE (line  275) - GND Clamp Typical data is non-monotonic
NOTE (line  276) - GND Clamp Maximum data is non-monotonic
NOTE (line  493) - ISSO_PU Maximum data is non-monotonic
NOTE (line  494) - ISSO_PU Typical data is non-monotonic
NOTE (line  494) - ISSO_PU Minimum data is non-monotonic
NOTE (line  538) - ISSO_PD Minimum data is non-monotonic
NOTE (line  541) - ISSO_PD Typical data is non-monotonic
NOTE (line  541) - ISSO_PD Maximum data is non-monotonic
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation


 init: begin read circuit files, cpu clock= 1.73E-01                            

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

Checking C:\Users\sh3qm\PycharmProjects\s2ibispy\tests\buffer_sp_files\driver_s2i\buffer.ibs for IBIS 7.1 Compatibility...

NOTE (line   60) - Pulldown Typical data is non-monotonic
NOTE (line   60) - Pulldown Maximum data is non-monotonic
NOTE (line   65) - Pulldown Minimum data is non-monotonic
NOTE (line  151) - Pullup Typical data is non-monotonic
NOTE (line  154) - Pullup Maximum data is non-monotonic
NOTE (line  225) - Pullup Minimum data is non-monotonic
NOTE (line  265) - GND Clamp Minimum data is non-monotonic
NOTE (line  275) - GND Clamp Typical data is non-monotonic
NOTE (line  276) - GND Clamp Maximum data is non-monotonic
NOTE (line  493) - ISSO_PU Maximum data is non-monotonic
NOTE (line  494) - ISSO_PU Typical data is non-monotonic
NOTE (line  494) - ISSO_PU Minimum data is non-monotonic
NOTE (line  538) - ISSO_PD Minimum data is non-monotonic
NOTE (line  541) - ISSO_PD Typical data is non-monotonic
NOTE (line  541) - ISSO_PD Maximum data is non-monotonic
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation

Errors  : 0
Warnings: 2

File Passed


 init: end read circuit files, cpu clock= 2.22E-01 peak memory=      72 mb      

 init: begin check errors, cpu clock= 2.22E-01                                  

 init: end check errors, cpu clock= 2.68E-01 peak memory=      74 mb            

 init: begin setup matrix, pivot=     0 cpu clock= 2.68E-01                     

       establish matrix -- done, cpu clock= 2.68E-01 peak memory=      75 mb    

       re-order matrix -- done, cpu clock= 2.69E-01 peak memory=      75 mb     

 init: end setup matrix, cpu clock= 2.70E-01 peak memory=      75 mb            

 dcop: begin dcop, cpu clock= 2.87E-01                                          

 dcop: end dcop, cpu clock= 3.00E-01 peak memory=      75 mb tot_iter=      94  

 output: C:\Users\sh3qm\PycharmProjects\s2ibispy\tests\buffer_sp_files\driver_s2

 sweep: tran tran0    begin, stop_t=  5.00E-08 #sweeps=**** cpu clock= 3.01E-01 

 tran: time= 5.0826E-09 tot_iter=     430 conv_iter=     170 cpu clock= 3.42E-01

 tran: time= 1.0026E-08 tot_iter=     784 conv_iter=     347 cpu clock= 3.64E-01

 tran: time= 1.5054E-08 tot_iter=     836 conv_iter=     373 cpu clock= 3.68E-01

 tran: time= 2.0329E-08 tot_iter=    1349 conv_iter=     559 cpu clock= 4.09E-01

 tran: time= 2.5020E-08 tot_iter=    1683 conv_iter=     726 cpu clock= 4.33E-01

 tran: time= 3.0081E-08 tot_iter=    2069 conv_iter=     877 cpu clock= 4.70E-01

 tran: time= 3.5004E-08 tot_iter=    2441 conv_iter=    1034 cpu clock= 5.05E-01

 tran: time= 4.0021E-08 tot_iter=    2607 conv_iter=    1117 cpu clock= 5.17E-01

 tran: time= 4.5250E-08 tot_iter=    2766 conv_iter=    1184 cpu clock= 5.32E-01

 tran: time= 5.0000E-08 tot_iter=    2905 conv_iter=    1248 cpu clock= 5.45E-01

 sweep: tran tran0    end, cpu clock= 5.45E-01 peak memory=      75 mb          

>info:         ***** hspice job concluded                                       

           total cpu time            0.45 seconds                               

           total elapsed time            0.55 seconds                           

           job started at     14:36:54 12/06/2025                               

           job ended   at     14:36:54 12/06/2025                               
>info:         ***** hspice job concluded


 lic: Release hspice token(s) 
