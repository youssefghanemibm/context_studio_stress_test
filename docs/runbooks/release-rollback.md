# Release rollback

1. Roll back with `oc rollout undo` to the previous ReplicaSet.
2. Check that database migrations of the failed release are backward compatible before rolling back.
3. Raise a problem record and attach the release notes of the failed release.
