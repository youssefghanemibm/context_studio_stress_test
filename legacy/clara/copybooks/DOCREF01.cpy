000100* ===============================================================*
000200* COPYBOOK   : DOCREF01                                          *
000300* DB2 TABLE  : CLR.T_DOCUMENT_REF                                *
000400* CONTENT    : DOCUMENT REFERENCES (DOCSTOR / EVIDENCE VAULT     *
000500*              IDS)                                              *
000600* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000700* ===============================================================*
000800 01  DOCREF01-REC.
000900     05  DOCR-DOC-REF-ID               PIC S9(18) COMP.
001000     05  DOCR-CLAIM-ID                 PIC X(12).
001100     05  DOCR-VAULT-OBJECT-ID          PIC X(36).
001200     05  DOCR-DOC-TYPE-CD              PIC X(4).
001300     05  DOCR-RECEIVED-TS              PIC X(26).
001400     05  DOCR-LAST-UPD-TS              PIC X(26).
001500     05  DOCR-LAST-UPD-PGM             PIC X(8).
001600     05  DOCR-LAST-UPD-USER            PIC X(8).
