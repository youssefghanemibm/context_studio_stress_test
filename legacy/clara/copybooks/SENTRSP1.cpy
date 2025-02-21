000100* ================================================================
000200* COPYBOOK   : SENTRSP1
000300* TYPE       : INTERFACE RECORD LAYOUT
000400* CONTENT    : SENTINEL SCORE RESPONSE
000500* ================================================================
000600 01  SENT-RESPONSE.
000700     05  SS-CLAIM-ID                   PIC X(12).
000800     05  SS-SCORE                      PIC 9(3).
000900     05  SS-MODEL-VERSION              PIC X(8).
001000     05  SS-REASON-1                   PIC X(6).
001100     05  SS-REASON-2                   PIC X(6).
