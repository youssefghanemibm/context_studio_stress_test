//CLRWPAY1 JOB (CLR,PROD),'VENDOR PAYMENT RUN',CLASS=C,MSGCLASS=X,
//             MSGLEVEL=(1,1),REGION=0M,NOTIFY=&SYSUID
//* ------------------------------------------------------------------*
//* JOB       : CLRWPAY1                                              *
//* FUNCTION  : VENDOR PAYMENT RUN                                    *
//* SCHEDULE  : THU 15:00 (BATCH SCHEDULER)                           *
//* SUPPORT   : MAINFRAME BATCH OPERATIONS                            *
//* STEPS     : STEP010 CLRST110 VENDOR INVOICE PAYMENT RUN           *
//* ------------------------------------------------------------------*
//* SITE SYMBOLS (HLQS, DB2 SUBSYSTEM AND PLAN) COME FROM THE INCLUDE
//         INCLUDE MEMBER=CLRSYMS
//JOBLIB   DD DSN=&CLRHLQ..LOADLIB,DISP=SHR
//         DD DSN=&DB2HLQ..SDSNLOAD,DISP=SHR
//*
//* STEP010 - VENDOR INVOICE PAYMENT RUN
//*
//STEP010  EXEC PGM=IKJEFT01,DYNAMNBR=20
//SYSTSPRT DD SYSOUT=*
//SYSPRINT DD SYSOUT=*
//SYSOUT   DD SYSOUT=*
//SYSUDUMP DD SYSOUT=D
//RPTOUT   DD SYSOUT=*
//SYSTSIN  DD *,SYMBOLS=JCLONLY
  DSN SYSTEM(&DB2SSID)
  RUN PROGRAM(CLRST110) PLAN(&DB2PLAN) -
      LIB('&CLRHLQ..LOADLIB')
  END
/*
//
