# Cutover and rollback design

`07_app_cutover.py` validates instance tags and comparison evidence, then performs a two-phase target transition for the APP01 IIS and nginx target groups. Registration precedes deregistration. Each target group must report healthy within the timeout. A failure automatically stops before source deregistration; it does not hide partial state.

`--action rollback` reverses the target order and uses the same health checks. The script writes an audit JSON containing before/after target health and endpoint probes.

This models a stateless web tier. It does not model sessions, queues, file shares, DNS caches, or database writes; those require workload-specific design.
