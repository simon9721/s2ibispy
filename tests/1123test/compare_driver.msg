

****** PrimeSim HSPICE -- T-2022.06 win64 (May 20 2022 7637141) ******          

 Input File: C:\Users\sh3qm\PycharmProjects\s2ibispy\tests\1123test\compare_driv

 lic:  

 lic: FLEXlm: SDK_12.10 

 lic: USER:   sh3qm                HOSTNAME: rd78ece-emclab 

 lic: HOSTID: 00ff89f5aa52         PID:      18212 

 lic: Using FLEXlm license file: 

 lic: 1704@synopsys.lic.mst.edu 

 lic: Checkout 1 hspice 

 lic: License/Maintenance for hspice will expire on 04-may-2026/2025.06 

 lic: 1(in_use)/50(total) FLOATING license(s) on SERVER 1704@synopsys.lic.mst.ed

 lic:   
Checking C:\Users\sh3qm\PycharmProjects\s2ibispy\tests\1123test\io_buf.ibs for IBIS 3.2 Compatibility...

WARNING (line   27) - Component 'MCM Driver 1' contains a blank character.
NOTE (line   74) - Pulldown Typical data is non-monotonic
NOTE (line   74) - Pulldown Maximum data is non-monotonic
NOTE (line   79) - Pulldown Minimum data is non-monotonic
NOTE (line  165) - Pullup Typical data is non-monotonic
NOTE (line  168) - Pullup Maximum data is non-monotonic
NOTE (line  239) - Pullup Minimum data is non-monotonic
NOTE (line  279) - GND Clamp Minimum data is non-monotonic
NOTE (line  289) - GND Clamp Typical data is non-monotonic
NOTE (line  290) - GND Clamp Maximum data is non-monotonic
WARNING - Model 'driver': Model_type 'I/O' must have Vinl set
WARNING - Model 'driver': Model_type 'I/O' must have Vinh set
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation


 init: begin read circuit files, cpu clock= 1.20E-01                            

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

       option post                                                              

       option probe                                                             

       option accurate                                                          

       option rmax =    0.500                                                   
IBISCHK7 V7.1.0

Checking C:\Users\sh3qm\PycharmProjects\s2ibispy\tests\1123test\io_buf.ibs for IBIS 3.2 Compatibility...

WARNING (line   27) - Component 'MCM Driver 1' contains a blank character.
NOTE (line   74) - Pulldown Typical data is non-monotonic
NOTE (line   74) - Pulldown Maximum data is non-monotonic
NOTE (line   79) - Pulldown Minimum data is non-monotonic
NOTE (line  165) - Pullup Typical data is non-monotonic
NOTE (line  168) - Pullup Maximum data is non-monotonic
NOTE (line  239) - Pullup Minimum data is non-monotonic
NOTE (line  279) - GND Clamp Minimum data is non-monotonic
NOTE (line  289) - GND Clamp Typical data is non-monotonic
NOTE (line  290) - GND Clamp Maximum data is non-monotonic
WARNING - Model 'driver': Model_type 'I/O' must have Vinl set
WARNING - Model 'driver': Model_type 'I/O' must have Vinh set
WARNING - Model 'driver': Vmeas timing test load parameter should be specified
NOTE - Combined Pulldown for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Typical data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Minimum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pulldown for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation
NOTE - Combined Pullup for Model: driver Maximum data is non-monotonic based on piece-wise linear interpolation

Errors  : 0
Warnings: 8

File Passed


 init: end read circuit files, cpu clock= 1.28E-01 peak memory=      71 mb      

 init: begin check errors, cpu clock= 1.28E-01                                  

 init: end check errors, cpu clock= 1.42E-01 peak memory=      72 mb            

 init: begin setup matrix, pivot=     0 cpu clock= 1.42E-01                     

       establish matrix -- done, cpu clock= 1.43E-01 peak memory=      72 mb    

       re-order matrix -- done, cpu clock= 1.43E-01 peak memory=      72 mb     

 init: end setup matrix, cpu clock= 1.44E-01 peak memory=      73 mb            

 dcop: begin dcop, cpu clock= 1.53E-01                                          

 dcop: end dcop, cpu clock= 1.60E-01 peak memory=      73 mb tot_iter=      39  

 output: C:\Users\sh3qm\PycharmProjects\s2ibispy\tests\1123test\compare_driver.t

 sweep: tran tran0    begin, stop_t=  5.00E-08 #sweeps=**** cpu clock= 1.61E-01 

 tran: time= 5.0510E-09 tot_iter=     409 conv_iter=     155 cpu clock= 1.89E-01

 tran: time= 1.0031E-08 tot_iter=     693 conv_iter=     297 cpu clock= 2.03E-01

 tran: time= 1.5054E-08 tot_iter=     751 conv_iter=     326 cpu clock= 2.06E-01

 tran: time= 2.0155E-08 tot_iter=    1229 conv_iter=     499 cpu clock= 2.39E-01

 tran: time= 2.5004E-08 tot_iter=    1436 conv_iter=     602 cpu clock= 2.49E-01

 tran: time= 3.0025E-08 tot_iter=    1838 conv_iter=     760 cpu clock= 2.78E-01

 tran: time= 3.5083E-08 tot_iter=    2245 conv_iter=     940 cpu clock= 3.08E-01

 tran: time= 4.0055E-08 tot_iter=    2371 conv_iter=    1003 cpu clock= 3.14E-01

 tran: time= 4.5117E-08 tot_iter=    2607 conv_iter=    1096 cpu clock= 3.31E-01

 tran: time= 5.0000E-08 tot_iter=    2761 conv_iter=    1171 cpu clock= 3.43E-01

 sweep: tran tran0    end, cpu clock= 3.43E-01 peak memory=      73 mb          

>info:         ***** hspice job concluded                                       

           total cpu time            0.24 seconds                               

           total elapsed time            0.34 seconds                           

           job started at     14:07:29 11/23/2025                               

           job ended   at     14:07:29 11/23/2025                               
>info:         ***** hspice job concluded


 lic: Release hspice token(s) 
