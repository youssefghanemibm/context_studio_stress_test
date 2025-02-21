000100* ===============================================================*
000200* COPYBOOK   : CLRASG01                                          *
000300* DB2 TABLE  : CLR.T_ASSESSOR_ASSIGNMENT                         *
000400* CONTENT    : CLAIMS ASSESSOR APPOINTMENTS (INTERNAL AND        *
000500*              VENDOR)                                           *
000600* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000700* ===============================================================*
000800 01  CLRASG01-REC.
000900     05  ASG-ASSIGN-ID                 PIC S9(18) COMP.
001000     05  ASG-CLAIM-ID                  PIC X(12).
001100     05  ASG-ASSESSOR-ID               PIC X(8).
001200     05  ASG-VENDOR-CD                 PIC X(8).
001300     05  ASG-APPOINTED-TS              PIC X(26).
001400     05  ASG-SLA-DUE-DT                PIC X(10).
001500     05  ASG-VERSION-NO                PIC S9(4) COMP.
001600     05  ASG-LAST-UPD-TS               PIC X(26).
001700     05  ASG-LAST-UPD-PGM              PIC X(8).
001800     05  ASG-LAST-UPD-USER             PIC X(8).
