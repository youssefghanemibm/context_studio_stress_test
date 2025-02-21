000100* ===============================================================*
000200* COPYBOOK   : RPTRUN01                                          *
000300* DB2 TABLE  : CLR.T_REPORT_RUN                                  *
000400* CONTENT    : REPORT RUN LOG                                    *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  RPTRUN01-REC.
000800     05  RPTR-RUN-ID                   PIC S9(9) COMP.
000900     05  RPTR-REPORT-CD                PIC X(8).
001000     05  RPTR-RUN-TS                   PIC X(26).
001100     05  RPTR-ROW-COUNT                PIC S9(9) COMP.
001200     05  RPTR-RUN-STATUS               PIC X(2).
001300     05  RPTR-LAST-UPD-TS              PIC X(26).
001400     05  RPTR-LAST-UPD-PGM             PIC X(8).
001500     05  RPTR-LAST-UPD-USER            PIC X(8).
