//CLRDRSV9 JOB (CLR,PROD),'RESERVE PARALLEL-RUN',CLASS=B,MSGCLASS=X,
//             MSGLEVEL=(1,1),REGION=0M,NOTIFY=&SYSUID
//* ------------------------------------------------------------------*
//* JOB       : CLRDRSV9                                              *
//* FUNCTION  : RESERVE PARALLEL-RUN RECONCILIATION (RETIRED          *
//*             2026-08-28)                                           *
//* SCHEDULE  : DAILY 05:00 FOR THE RESERVE PARALLEL RUN              *
//*             2026-03-02 TO 2026-08-28                              *
//* STATUS    : RETIRED 2026-08-28 - PARALLEL RUN ENDED               *
//* SUPPORT   : MAINFRAME BATCH OPERATIONS                            *
//* STEPS     : STEP010 CLRRS210 RESERVE PARALLEL-RUN                 *
//*                              RECONCILIATION AGAINST               *
//*                              RESERVE-ENGINE (2026-03-02 TO        *
//*                              2026-08-28)                          *
//* ------------------------------------------------------------------*
//* SITE SYMBOLS (HLQS, DB2 SUBSYSTEM AND PLAN) COME FROM THE INCLUDE
//         INCLUDE MEMBER=CLRSYMS
//JOBLIB   DD DSN=&CLRHLQ..LOADLIB,DISP=SHR
//         DD DSN=&DB2HLQ..SDSNLOAD,DISP=SHR
//*
//* STEP010 - RESERVE PARALLEL-RUN RECONCILIATION AGAINST
//* RESERVE-ENGINE (2026-03-02 TO 2026-08-28)
//*
//STEP010  EXEC PGM=IKJEFT01,DYNAMNBR=20
//SYSTSPRT DD SYSOUT=*
//SYSPRINT DD SYSOUT=*
//SYSOUT   DD SYSOUT=*
//SYSUDUMP DD SYSOUT=D
//RPTOUT   DD SYSOUT=*
//SYSTSIN  DD *,SYMBOLS=JCLONLY
  DSN SYSTEM(&DB2SSID)
  RUN PROGRAM(CLRRS210) PLAN(&DB2PLAN) -
      LIB('&CLRHLQ..LOADLIB')
  END
/*
//
