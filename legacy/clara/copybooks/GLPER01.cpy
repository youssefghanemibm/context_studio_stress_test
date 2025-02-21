000100* ===============================================================*
000200* COPYBOOK   : GLPER01                                           *
000300* DB2 TABLE  : CLR.T_GL_PERIOD                                   *
000400* CONTENT    : GL PERIOD CONTROL                                 *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  GLPER01-REC.
000800     05  GLPE-GL-PERIOD                PIC X(6).
000900     05  GLPE-PERIOD-STATUS            PIC X(1).
001000     05  GLPE-CLOSED-TS                PIC X(26).
001100     05  GLPE-CLOSED-BY                PIC X(8).
001200     05  GLPE-LAST-UPD-TS              PIC X(26).
001300     05  GLPE-LAST-UPD-PGM             PIC X(8).
001400     05  GLPE-LAST-UPD-USER            PIC X(8).
