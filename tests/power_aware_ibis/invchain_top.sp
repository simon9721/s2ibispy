*.OPTIONS POST
.OPTIONS LIST NODE POST
.OPTIONS METHOD=GEAR
.OPTIONS GSHUNT=1E-12
*.OPTIONS SEARCH=' '  $This option must be present for decryption to work

.TITLE Nominal Full Drive

.PARAM  vccr_typ  = 1.300V
.PARAM  vccr_min  = 1.250V
.PARAM  vccr_max  = 1.350V

.PARAM  vccq_typ  = 1.800V
.PARAM  vccq_min  = 1.700V
.PARAM  vccq_max  = 1.900V

.PARAM  gnd       = 0.000V
.PARAM  vssq      = 0.000V
.PARAM  vss       = 0.000V

**** Match up typ, min, or max voltages for corner sims

***********************************************************
**** TOP CELL:  invchain
***********************************************************
*xi0 PAD vccq IN vssq invchain
XSPI_BUFFER VIN VOUT8 vccq vssq invchain