000100* ===============================================================*
000200* COPYBOOK   : RICESS01                                          *
000300* DB2 TABLE  : CLR.T_REINSURANCE_CESSION                         *
000400* CONTENT    : REINSURANCE CESSIONS                              *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  RICESS01-REC.
000800     05  RICE-CESSION-ID               PIC S9(18) COMP.
000900     05  RICE-CLAIM-ID                 PIC X(12).
001000     05  RICE-TREATY-CD                PIC X(8).
001100     05  RICE-CEDED-RSV-AMT            PIC S9(11)V99 COMP-3.
001200     05  RICE-CEDED-PAID-AMT           PIC S9(11)V99 COMP-3.
001300     05  RICE-REINSURER-CD             PIC X(8).
001400     05  RICE-LAST-UPD-TS              PIC X(26).
001500     05  RICE-LAST-UPD-PGM             PIC X(8).
001600     05  RICE-LAST-UPD-USER            PIC X(8).
