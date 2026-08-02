# Validation testing tasks

- [ ] 1. Launch VAL-APP01 and VAL-DATA01 from recorded upgraded AMIs after approval.
- [ ] 2. Wait for EC2 checks and SSM Online; capture instance IDs.
- [ ] 3. Run post-upgrade tests and compare with baseline.
- [ ] 4. Review Windows/application event errors and unexplained test differences.
- [ ] 5. Inject the VAL-APP01 Next.js service failure and verify a red result.
- [ ] 6. Ask Kiro to diagnose from evidence, restore the service, and rerun tests.
- [ ] 7. Record `pass`, `conditional`, or `blocked`; do not proceed on conditional/blocked without owner disposition.
