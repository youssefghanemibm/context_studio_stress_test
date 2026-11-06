# PostgreSQL point-in-time restore

1. Agree the restore point with the service owner and record it in the change ticket.
2. Scale the service to zero replicas before restoring its database.
3. Restore into a new cluster, validate row counts, then switch the service over.
4. Scale the service back to its production replica count.
