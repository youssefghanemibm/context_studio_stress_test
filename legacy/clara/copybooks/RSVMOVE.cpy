000100* ===============================================================*
000200* COPYBOOK   : RSVMOVE                                           *
000300* TYPE       : INTERFACE RECORD LAYOUT                           *
000400* CONTENT    : CLX-IF-042 FIXED-WIDTH RECORD (QUEUE              *
000500*              CLR.RSVMOVE.OUT)                                  *
000600* RECORD     : FIXED LENGTH, 116 BYTES                           *
000700* ---------------------------------------------------------------*
000800* CHANGE LOG                                                     *
000810* 2025-04-25 KBARR01  CHUB-138   RM-AMOUNT WIDENED TO            *
000820*                                S9(11)V99 (NORDIC LARGE LOSSES) *
000900* ===============================================================*
001000 01  RSVMOVE-REC.
001100     05  RM-HEADER.
001200         10  RM-REC-TYPE               PIC X(2).
001300         10  RM-EXTRACT-DATE           PIC X(10).
001400     05  RM-CLAIM-ID                   PIC X(12).
001500     05  RM-RSV-ID                     PIC S9(18) COMP.
001600     05  RM-MOVE-ID                    PIC S9(18) COMP.
001700     05  RM-MOVE-TYPE                  PIC X(2).
001800     05  RM-CURRENCY                   PIC X(3).
001900     05  RM-AMOUNT                     PIC S9(11)V99 COMP-3.      CHUB138
002000     05  RM-GBP-AMOUNT                 PIC S9(9)V99 COMP-3.
002100     05  RM-PRODUCT                    PIC X(6).
002200     05  RM-PERIL                      PIC X(4).
002300     05  RM-TIER                       PIC X(1).
002400     05  RM-MOVE-TS                    PIC X(26).
002500     05  FILLER                        PIC X(22).
