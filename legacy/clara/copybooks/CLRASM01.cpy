000100* ===============================================================*
000200* COPYBOOK   : CLRASM01                                          *
000300* DB2 TABLE  : CLR.T_ASSESSMENT                                  *
000400* CONTENT    : ASSESSMENT RECORDS                                *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  CLRASM01-REC.
000800     05  ASM-ASSESS-ID                 PIC S9(18) COMP.
000900     05  ASM-CLAIM-ID                  PIC X(12).
001000     05  ASM-ASSESS-TYPE-CD            PIC X(2).
001100     05  ASM-COVER-DECISION-CD         PIC X(2).
001200     05  ASM-ESTIMATE-AMT              PIC S9(11)V99 COMP-3.
001300     05  ASM-REPORT-RECEIVED-DT        PIC X(10).
001400     05  ASM-LAST-UPD-TS               PIC X(26).
001500     05  ASM-LAST-UPD-PGM              PIC X(8).
001600     05  ASM-LAST-UPD-USER             PIC X(8).
