000100* ===============================================================*
000200* COPYBOOK   : SENTREQ1                                          *
000300* TYPE       : INTERFACE RECORD LAYOUT                           *
000400* CONTENT    : SENTINEL SCORE REQUEST                            *
000500* ===============================================================*
000600 01  SENT-REQUEST.
000700     05  SR-CLAIM-ID                   PIC X(12).
000800     05  SR-PRODUCT                    PIC X(6).
000900     05  SR-PERIL                      PIC X(4).
001000     05  SR-LOSS-DATE                  PIC X(10).
001100     05  SR-NOTIFIED-TS                PIC X(26).
