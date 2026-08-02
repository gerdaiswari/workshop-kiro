# Validation testing requirements

## Objective
Prove or disprove compatibility on new validation instances without changing source traffic or data.

## Acceptance criteria

- Launch one validation instance from each upgraded AMI with IMDSv2, the SSM profile, encrypted storage, and the workload security group.
- Wait for EC2 running, status checks, and SSM Online before tests.
- Verify Windows caption/build indicates Server 2025 and free boot disk remains >=20 GiB.
- APP01: test IIS/Angular, Spring Boot/Actuator/API, Next.js/API, nginx proxy, and Windows services.
- DATA01: test XAMPP/PHP, all database services, expected seed row counts, and query checksums.
- Compare mandatory check IDs with baseline; missing tests are failures.
- Inject a stopped Next.js service on VAL-APP01, prove the suite fails, diagnose with Kiro, restore it, and prove the suite passes.
- Produce machine-readable evidence and a human-readable decision. No validation test may write to source systems.
