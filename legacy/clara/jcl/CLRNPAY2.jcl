//CLRNPAY2 JOB (CLR,PROD),'PAYMENT CONFIRMATION',CLASS=B,MSGCLASS=X,
//             MSGLEVEL=(1,1),REGION=0M,NOTIFY=&SYSUID
//* ------------------------------------------------------------------*
//* JOB       : CLRNPAY2                                              *
//* FUNCTION  : PAYMENT CONFIRMATIONS                                 *
//* SCHEDULE  : MON-FRI 07:30 (BATCH SCHEDULER)                       *
//* SUPPORT   : MAINFRAME BATCH OPERATIONS                            *
//* STEPS     : STEP010 CLRST050 PAYMENT CONFIRMATION IMPORT FROM     *
//*                              CPG (CLX-IF-020)                     *
//* ------------------------------------------------------------------*
//* SITE SYMBOLS (HLQS, DB2 SUBSYSTEM AND PLAN) COME FROM THE INCLUDE
//         INCLUDE MEMBER=CLRSYMS
//JOBLIB   DD DSN=&CLRHLQ..LOADLIB,DISP=SHR
//         DD DSN=&DB2HLQ..SDSNLOAD,DISP=SHR
//*
//* STEP010 - PAYMENT CONFIRMATION IMPORT FROM CPG (CLX-IF-020)
//*
//STEP010  EXEC PGM=IKJEFT01,DYNAMNBR=20
//SYSTSPRT DD SYSOUT=*
//SYSPRINT DD SYSOUT=*
//SYSOUT   DD SYSOUT=*
//SYSUDUMP DD SYSOUT=D
//RPTOUT   DD SYSOUT=*
//IMPIN    DD DSN=&CLRHLQ..CLRST050.IMPIN(0),DISP=SHR
//SYSTSIN  DD *,SYMBOLS=JCLONLY
  DSN SYSTEM(&DB2SSID)
  RUN PROGRAM(CLRST050) PLAN(&DB2PLAN) -
      LIB('&CLRHLQ..LOADLIB')
  END
/*
//
