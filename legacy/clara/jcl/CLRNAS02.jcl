//CLRNAS02 JOB (CLR,BATCH),'VENDOR INVOICE MATCH',CLASS=C,MSGCLASS=X,
//             MSGLEVEL=(1,1),REGION=0M,NOTIFY=&SYSUID
//* ------------------------------------------------------------------*
//* JOB       : CLRNAS02                                              *
//* FUNCTION  : VENDOR INVOICE MATCHING                               *
//* SCHEDULE  : MON-FRI 01:00 (BATCH SCHEDULER)                       *
//* SUPPORT   : MAINFRAME BATCH OPERATIONS                            *
//* STEPS     : STEP010 CLRAS070 VENDOR INVOICE MATCHING (ASSESSOR    *
//*                              FEES, CLX-IF-016)                    *
//* ------------------------------------------------------------------*
//* SITE SYMBOLS (HLQS, DB2 SUBSYSTEM AND PLAN) COME FROM THE INCLUDE
//         INCLUDE MEMBER=CLRSYMS
//JOBLIB   DD DSN=&CLRHLQ..LOADLIB,DISP=SHR
//         DD DSN=&DB2HLQ..SDSNLOAD,DISP=SHR
//*
//* STEP010 - VENDOR INVOICE MATCHING (ASSESSOR FEES, CLX-IF-016)
//*
//STEP010  EXEC PGM=IKJEFT01,DYNAMNBR=20
//SYSTSPRT DD SYSOUT=*
//SYSPRINT DD SYSOUT=*
//SYSOUT   DD SYSOUT=*
//SYSUDUMP DD SYSOUT=D
//RPTOUT   DD SYSOUT=*
//SYSTSIN  DD *,SYMBOLS=JCLONLY
  DSN SYSTEM(&DB2SSID)
  RUN PROGRAM(CLRAS070) PLAN(&DB2PLAN) -
      LIB('&CLRHLQ..LOADLIB')
  END
/*
//
