# Release Checklist

Do not release solely because CI is green.

## Before merge
- [ ] Acceptance criteria mapped to test results.
- [ ] Unit/integration/browser tests run as applicable.
- [ ] Independent check used for high-impact calculations.
- [ ] Security/privacy review completed for sensitive changes.
- [ ] No secrets or customer data in diff, logs, fixtures, or artifacts.
- [ ] Documentation and known limitations updated.
- [ ] UI/export artifacts inspected when changed.

## Before a customer pilot
- [ ] Scope and exclusions agreed with customer.
- [ ] Input/output handling and retention explained.
- [ ] Original files preserved and hashed.
- [ ] Human-review responsibilities explicit.
- [ ] A failed run can be reported without fabricating a pass.
- [ ] Reproduction and support contact documented.

## Before production hosting (not currently in scope)
- [ ] Threat model and security review approved.
- [ ] Authentication, authorization, tenant isolation and audit logging tested.
- [ ] Retention/deletion and backup/restore tested.
- [ ] Monitoring, incident response and rollback practiced.
- [ ] Rate/cost limits and abuse controls set.
- [ ] Privacy terms and customer data handling reviewed.
- [ ] Deployment and recovery tested in a staging environment.

## Rollback plan
For a hosted release, identify the last known-good version, data migrations, backward compatibility, and rollback owner before deploy. Do not roll back database state blindly. For the current local-first prototype, distribute a known-good package and preserve the input files and prior reports.
