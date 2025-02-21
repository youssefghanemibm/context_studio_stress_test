000100* ================================================================
000200* COPYBOOK   : CLRDATE1
000300* TYPE       : COMMON WORK AREA
000400* CONTENT    : DATE WORK AREA
000500* ================================================================
000600 01  CLR-DATE-WORK.
000700     05  DW-IN-DATE                    PIC X(10).
000800     05  DW-CALENDAR                   PIC X(2).
000900     05  DW-BUS-DAYS                   PIC S9(4) COMP.
001000     05  DW-OUT-DATE                   PIC X(10).
