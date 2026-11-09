# Security and trading-risk reports

Do not publish passwords, captcha images/codes, tokens, cookies, account
identifiers, full requests/responses, trading records or unsanitized tracebacks.
Never send credentials to maintainers, in issues, PRs, CI artifacts or email.

For a vulnerability, possible disclosure, duplicate-submission risk or account
mixing, contact the repository maintainer privately at **riiyzhou@gmail.com**
(the project's published author address). Send only a sanitized initial summary,
affected versions and a synthetic reproduction; arrange an appropriate private
follow-up channel before sharing further details. Inbox availability and response
times are not verified or guaranteed by CI; no SLA is promised.

GitHub Private Vulnerability Reporting was disabled at the 2026-11-08 read-only
check. If the maintainer later enables it, GitHub's private report interface can
be used instead; do not mistake a public issue for a private report. This Build
does not change repository security settings.

The maintainer triages security and trading risk promptly when available,
records affected versions/impact/mitigation, assesses yanking or warnings and
coordinates a uniquely versioned Hotfix and sanitized advisory. Stop affected
automation while the outcome is uncertain; never automatically retry an order
or imply that reinstalling the SDK can reverse broker orders or funds changes.

Normal maintenance targets the current stable release; Beta is opt-in with no
production assurance. Older versions are best effort, without an unresourced
long-term support commitment. Historical 0.2.6 predates P0-P3 protections and is
not a default safe downgrade. Known dependency advisories must be assessed
before public 0.3.0 Beta/Stable; see
[P4 dependency review](docs/refactor/reports/P4-dependency-review.md).
