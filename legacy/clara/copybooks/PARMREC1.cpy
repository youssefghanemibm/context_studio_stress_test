000100* ===============================================================*
000200* COPYBOOK   : PARMREC1                                          *
000300* DB2 TABLE  : CLR.T_PARAM                                       *
000400* CONTENT    : BUSINESS PARAMETERS WITH VALIDITY DATES (READ     *
000500*              VIA CLRCM040)                                     *
000600* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000700* ===============================================================*
000800 01  PARMREC1-REC.
000900     05  PARM-PARAM-KEY                PIC X(20).
001000     05  PARM-VALID-FROM               PIC X(10).
001100     05  PARM-VALID-TO                 PIC X(10).
001200     05  PARM-PARAM-VALUE              PIC X(40).
001300     05  PARM-PARAM-DESC               PIC X(120).
001400     05  PARM-CHANGE-TICKET            PIC X(10).
001500     05  PARM-CHANGED-BY               PIC X(8).
