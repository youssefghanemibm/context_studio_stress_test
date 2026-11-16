# Schema-assistant prompt

Paste the prompt below into the product's schema-assistant chat. Then compare the schema the assistant builds with `corvane_claims.jsonld`. Judge the saved schema (export it or reopen it), not the chat reply.

## Prompt

Build a knowledge-graph schema for an insurer's claims-platform modernisation: a legacy COBOL/CICS/DB2 mainframe being replaced by Java microservices.

Node types: Person, Team, Department, Location, Organisation, System, Program, Copybook, Batch Job, Screen Map, Database Table, Interface, Service, Kafka Topic, Business Rule, Rule Version, Regulation, Regulatory Report, Product, Claim Type, Process Stage, Process Step, Claims Assessor, Claim, Incident, Architecture Decision, Ticket, Milestone.

Relationships (subject → object): REPORTS_TO (Person → Person), MEMBER_OF (Person → Team), OWNS_PROCESS (Person → Process Stage), WRITES_TO_TABLE (Program → Database Table), CALLS_PROGRAM (Program → Program), RUNS_PROGRAM (Batch Job → Program), SOURCE_SYSTEM and TARGET_SYSTEM (Interface → System), DEPENDS_ON_INTERFACE (Interface → Interface), FEEDS_REPORT (Interface → Regulatory Report), REPLACES_PROGRAM (Service → Program), HAS_VERSION (Business Rule → Rule Version), SUPERSEDES (Business Rule → Business Rule), GOVERNED_BY (Business Rule → Regulation), APPOINTED_ASSESSOR (Claim → Claims Assessor).

Keep every node type and relationship name exactly as written: same spelling and case, no renaming or merging, and no generic relationships such as BELONGS_TO or RELATES_TO. Store dates, thresholds, statuses, schedules and aliases as properties, not nodes. Show me the complete saved schema.

## Follow-up prompts

Send these one at a time, after the schema is saved. After each one, check the saved schema, not the chat reply.

1. Rename the relationship WRITES_TO_TABLE to UPDATES_TABLE and show me the saved schema.
2. Rename the node type Screen Map to Terminal Screen, keep its relationships, and show me the saved schema.
3. Undo both renames (UPDATES_TABLE back to WRITES_TO_TABLE, Terminal Screen back to Screen Map). Then list every node type and relationship name in the saved schema.

Record three things: whether each rename reached the saved schema, whether any old name was left behind as a duplicate, and whether relationships stayed attached to the renamed node type.
