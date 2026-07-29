# Cutover and rollback tasks

- [ ] 1. Confirm APP01 post comparison passes and VAL-APP01 is SSM Online.
- [ ] 2. Show target health, exact command, rollback command, and monitoring window.
- [ ] 3. Obtain explicit approval and run `python3 scripts/07_app_cutover.py --action cutover ...`.
- [ ] 4. Run external ALB endpoint probes and observe for the workshop window.
- [ ] 5. Demonstrate rollback after separate explicit approval, or leave source registered according to instructor choice.
- [ ] 6. Record measured transition and recovery times; never call rollback instant.
- [ ] 7. Write a production DATA01 cutover design, but execute no DATA01 cutover.

> Do not use unattended `/spec run cutover-rollback` with broad tool trust.
