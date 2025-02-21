000100* ===============================================================*
000200* COPYBOOK   : CLRERR01                                          *
000300* TYPE       : COMMON WORK AREA                                  *
000400* CONTENT    : ERROR BLOCK                                       *
000500* ===============================================================*
000600 01  CLR-ERROR-BLOCK.
000700     05  ERR-PGM                       PIC X(8).
000800     05  ERR-SQLCODE                   PIC S9(9) COMP.
000900     05  ERR-PARA                      PIC X(30).
001000     05  ERR-TEXT                      PIC X(120).
