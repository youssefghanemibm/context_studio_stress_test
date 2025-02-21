000100* ===============================================================*
000200* COPYBOOK   : MQMDCLR1                                          *
000300* TYPE       : COMMON WORK AREA                                  *
000400* CONTENT    : MQ MESSAGE DESCRIPTOR WRAPPER                     *
000500* ===============================================================*
000600 01  CLR-MQ-AREA.
000700     05  MQ-QUEUE-NAME                 PIC X(48).
000800     05  MQ-MSG-LEN                    PIC S9(9) COMP.
000900     05  MQ-CORREL-ID                  PIC X(24).
