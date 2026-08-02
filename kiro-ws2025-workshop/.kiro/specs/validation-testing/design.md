# Validation testing design

`05_launch_validation.py` reads successful upgrade evidence and launches tagged instances from upgraded AMIs. It does not reuse source private IPs, DNS names, or identity integrations. Test scripts execute locally through SSM, so database ports remain closed.

`03_run_tests.py --phase post` captures normalized checks with stable IDs. `06_compare_results.py` compares baseline and post by ID and value, allowing OS-version checks to have phase-specific expected values. A decision is pass only when every mandatory post check passes and no mandatory baseline behavior disappeared.

Failure injection is validation-only and requires the target tag `Role=VAL-APP01`.
