//CLRNRSV3 JOB (CLR,BATCH),'RESERVE MOVEMENT EXT',CLASS=B,MSGCLASS=X,
//             MSGLEVEL=(1,1),REGION=0M,NOTIFY=&SYSUID
//* ------------------------------------------------------------------*
//* JOB       : CLRNRSV3                                              *
//* FUNCTION  : RESERVE MOVEMENT EXTRACT (CLX-IF-042)                 *
//* SUPPORT   : MAINFRAME BATCH OPERATIONS                            *
//* STEPS     : STEP010 CLRRS170 DAILY RESERVE MOVEMENT EXTRACT       *
//*                              (CLX-IF-042)                         *
//* RESTART   : RERUN THE WHOLE JOB; CLRRS170 ONLY EXTRACTS ROWS      *
//*             WITH EXTRACTED_FLAG = 'N'.                            *
//* ------------------------------------------------------------------*
//* SITE SYMBOLS (HLQS, DB2 SUBSYSTEM AND PLAN) COME FROM THE INCLUDE
//         INCLUDE MEMBER=CLRSYMS
//JOBLIB   DD DSN=&CLRHLQ..LOADLIB,DISP=SHR
//         DD DSN=&DB2HLQ..SDSNLOAD,DISP=SHR
//*
//* STEP010 - DAILY RESERVE MOVEMENT EXTRACT (CLX-IF-042)
//*
//STEP010  EXEC PGM=IKJEFT01,DYNAMNBR=20
//SYSTSPRT DD SYSOUT=*
//SYSPRINT DD SYSOUT=*
//SYSOUT   DD SYSOUT=*
//SYSUDUMP DD SYSOUT=D
//RPTOUT   DD SYSOUT=*
//RSVOUT   DD DSN=CLR.PROD.RSVMOVE.DAILY(+1),
//            DISP=(NEW,CATLG,DELETE),UNIT=SYSDA,
//            SPACE=(CYL,(20,10),RLSE),
//            DCB=(RECFM=FB,LRECL=116,BLKSIZE=0)
//SYSTSIN  DD *,SYMBOLS=JCLONLY
  DSN SYSTEM(&DB2SSID)
  RUN PROGRAM(CLRRS170) PLAN(&DB2PLAN) -
      LIB('&CLRHLQ..LOADLIB')
  END
/*
//
