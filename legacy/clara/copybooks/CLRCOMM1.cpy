000100* ===============================================================*
000200* COPYBOOK   : CLRCOMM1                                          *
000300* TYPE       : CICS COMMAREA                                     *
000400* CONTENT    : COMMON CICS COMMAREA                              *
000500* ===============================================================*
000600 01  CLR-COMMAREA.
000700     05  CA-TRANID                     PIC X(4).
000800     05  CA-USER-ID                    PIC X(8).
000900     05  CA-CLAIM-ID                   PIC X(12).
001000     05  CA-RETURN-CD                  PIC S9(4) COMP.
001100     05  CA-MSG                        PIC X(79).
