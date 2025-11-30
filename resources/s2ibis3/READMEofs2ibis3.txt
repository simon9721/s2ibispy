This README file describes the v1.1 distribution of s2ibis3.


This directory contains the s2ibis3 Java application. 

This utilitiy has been tested for Sun Solaris (5.7), Linux 2.4.18 and Windows XP.

To install S2IBIS3, simply unpack the zip file. This distribution contains:

README		this file.
s2ibis3.csh	Run this file to execute s2ibis3 for linux or unix
s2ibis3.bat	Run this file to execute s2ibis3 for Windows
s2ibis3.txt	An explanation of the command structure for the s2i file and the 
		key features and differences of s2ibis3 as compared with s2ibis2.
curves.txt	An explaination of how the various curves are obtained in s2ibis3.

modification_v1.1.txt An explanation of the changes made to s2ibis3 in the latest revision (v1.1).

java		directory with java source code and class files.
		The source code can be modified and recompiled using 
		Java sdk 1.4.0.
		The source code consists of 
		1)s2iHeader.java
		2)s2iutil.java				
		3)s2ispice.java
		4)s2ianalyz.java
		5)s2iParser.java
		6)s2ibis3.java

example	        example directory with 4 sub-dirs ex1, ex2, ex3 and ex4.

ex1		Directory with a sample buffer.s2i file along with a buffer.ibs
		file. it also has the buffer.sp, spectre.mod and hspice.mod files 
		to be able to run the example properly.

ex2		Repeat of ex1 run with Hspice with a slightly better model.

ex3		Directory with similar files as above and an extra netlist file
		that has the netlist of the parallel_mosfet. This is needed for
		demonstrating the working of the [Series MOSFET] keyword.

ex4		Directory with tri-state drivers show how multiple Vdd's can be
		used using the [Pin Map] keyword. This example uses HSpice.

---------------------------------------------------------------------------------		
Requirements:	To run s2ibis3, Java2, version 1.4.0 must be installed. 
		A minimum of Java 2 Runtime Environment(JRE), version 1.4.x.
		must be installed to be able to run s2ibis3. Users could also
		install Java 2 Standard Development Kit (SDK) version 1.4.x.
		This is preferred over the JRE as the user could modify a java
		file and recompile the code. Java JRE or SDK could be downloaded
		free from http://java.sun.com
		s2ibis3 assumes that the spice engines are set in the path
		variables and ready for use.
		
		This version has been tested on HSpice ver 2001.2 

Compiling the Code : If the code has to be compiled, it must be compiled in the
		     following order -s2iHeader.java, s2iutil.java,
		     s2ispice.java, s2ianalyz.java, s2iParser.java and
		     s2ibis3.java. If this order is not followed, compilation
		     error could be experienced.
		
Running S2ibis3	: sun/linux/unix
			-To run s2ibis3, type the following on the command line:
			% s2ibis3.csh -s2ibis3 buffer.s2i
			where buffer.s2i is the s2i command file as discussed in
			the s2ibis3.txt
			-If there is a 'permission denied' error when running the
			.csh file, change permissions by doing 
			% chmod 744 s2ibis3.csh
			-If it is desired, s2ibis3 could be run from a different
			directory from the installation directory by using the
			'-root' switch with s2ibis3.csh as this example suggest:
			% s2ibis3 -root ../../s2i_install_dir -s2ibis3 buffer.s2i
			
			
		  windows
		   	-most of the instruction for unix apply for windows users as well.
			-To run s2ibis3, type the following on the command prompt:
			% s2ibis3.bat -s2ibis3 buffer.s2i
			-If the path variables are not set for java and the spice engines, 
			read instructions at http://java.sun.com/j2se/1.4.2/install-windows.html
			on how to set path variables for windows. s2ibis3 would not run if paths have
			not been set properly.
[note] % is not needed to be inserted in the command line.			
-----------------------------------------------------------------------------
Known Problems and Bugs.
-

-----------------------------------------------------------------------------			
You are free to use, modify, and redistribute this software. See the copyright legends contained
in the source code.

If you have comments, bug reports, or suggestions for features, please
email them to me at:
akvarma@ncsu.edu
February '05
