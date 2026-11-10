Release and maintenance
=======================

Status and support
------------------

The current internal candidate is 0.3.0a1 (unpublished). The planned next stable
target is 0.3.0, preceded by PyPI Beta 0.3.0b1; neither upload is authorized.
Only CPython 3.11 / Linux is the support target. Other platforms/versions
remain unverified. Tests are synthetic and offline, not evidence of broker
protocol correctness or real execution.
Read the Docs is canonical; GitHub Pages is a mirror. HTML + RST + Sphinx only.

Version and immutable tags
--------------------------

Use PEP 440: 0.3.0a1, 0.3.0b1, 0.3.0rc1, 0.3.0; tags are v-prefixed canonical
versions. setuptools_scm writes the runtime version; a source archive without Git
must preserve its PKG-INFO/generated version. Untagged internal snapshots may
have a development version and must not be presented as a tagged release.
Update fallback/candidate fields, docs, cookiecutter and bumpversion together;
use bumpversion only with ``--no-commit --no-tag`` and inspect the diff. README's
commits-since badge stays at the last actually published tag until publication.
Never overwrite tags, reuse versions, or use ``skip-existing`` to hide conflicts.

Alpha and Beta gates
--------------------

Alpha is internal: clean checkout, check/docs/Offline CI, one sdist and one wheel,
strict metadata/content audit, independent fresh venv installs, ``pip check``,
matching runtime/distribution versions, API/CLI help and constructor smoke under
OS-level network denial. Record commit, tool versions, commands, SHA256, file
lists and installation evidence. No real credentials or broker calls.

Beta requires a separate maintainer upload decision after Alpha and independent
review. The planned explicit opt-in command (not available until upload) is::

    python -m pip install --pre emtl==0.3.0b1

Beta notes must name version, date, commit, hashes, environment, changes,
compatibility limits, upgrade/downgrade risks and known issues. Collect feedback
for a suggested ten working days. If no useful feedback arrives, the maintainer
explicitly chooses further observation, pause or stable consideration; silence
does not validate real trading. Classify feedback as installation/environment,
documentation, API compatibility, defect or security/trading risk.

Feedback template: emtl/Python/OS versions; install method; synthetic minimal
reproduction; expected/actual behavior; sanitized exception category. Never submit
passwords, captcha data, tokens, cookies, account identifiers, full requests or
responses, or trading records. Do not request live login/order/cancel results.
All blockers (leakage, duplicate-submit risk, account mixing, unintended API
breakage) must be resolved; deferrals need explicit approval and disclosure.
Stable requires an explicit post-Beta approval; channel selection is not upload
authorization.

Release checklist
-----------------

The maintainer is responsible for every release decision:

#. Confirm candidate is a clean, merged master commit, with successful required
   Build/check/docs, Offline and Package Alpha workflows at that exact SHA (not just a PR head).
#. Build once, validate and install those exact artifacts; publish only the same
   SHA256-verified files. Archive logs, JUnit, coverage, manifests and tool versions.
#. Confirm tag, SCM, sdist, wheel, runtime version, Changelog and release notes agree.
   Manual dispatch must run from master at the exact tagged commit: GitHub's event
   SHA must equal the tested checkout SHA so Trusted Publishing provenance does
   not identify a later master commit. If master has already advanced before
   dispatch, stop and prepare a new approved candidate; do not relabel evidence.
#. Confirm protected ``pypi`` environment has active required reviewers. OIDC belongs
   only to Publish; PRs never get publishing rights. No long-lived PyPI token.
   Stage validators from the trusted master/workflow commit outside the workspace
   before checking out a candidate. Run them in isolated Python; never let an
   unmerged candidate replace its own ancestry/approval validator or install
   candidate-supplied build requirements before those checks.
#. Obtain separate approval before any tag push, Beta upload, Stable upload or
   GitHub Release. A tag alone must not authorize upload.
#. After authorized publication, compare PyPI filenames/hashes and provenance
   repository/workflow/commit, then install that exact version from PyPI in fresh
   environments and run the same network-disabled smoke. Record PyPI URL, workflow
   run, artifact ID, tag and commit. Package publication is not contingent on a
   successful mirror deployment; repair docs independently.


PyPI environment approval probe (no upload)
-------------------------------------------

The no-upload approval probe passed on 2026-11-10: `run #42780759403
<https://github.com/riiy/emtl/actions/runs/42780759403>`_ on master commit
``8f654edbec6f29d4e39e5b63e6ad2d2b8ed28191`` was approved for ``pypi``
by ``riiy`` and completed successfully. This validates the gate for that run,
not a PyPI upload or independent second-person review. Details are recorded in
``docs/refactor/reports/P4-acceptance.md``.

If the ``pypi`` protection rules change, repeat this no-upload verification
without exercising the Release workflow or PyPI:

#. From the ``master`` branch, open Actions → PyPI Environment Approval Probe
   → Run workflow, and set ``run_probe=true``.
#. Confirm the ``approval-probe`` job enters Waiting for approval before any
   step runs.
#. Have a configured reviewer approve the deployment; confirm the job completes
   and its log states that no checkout, OIDC permission, package build, PyPI
   token or upload was used.
#. Archive the run URL, head SHA, approval API record, job log and final result
   in ``P4-acceptance.md``. Record the waiting state/timestamp when captured;
   do not infer missing timestamps.

The probe requests no additional token permissions (``permissions: {}``;
GitHub retains ``metadata: read``), no OIDC permission, no package build and
no upload step. It exists only to test the GitHub Environment protection
rule. A skipped probe (input false) is not approval evidence. Do not use a
real Beta/Stable release to test protection.

Failure, rollback and Hotfix
----------------------------

Build/test failure: stop, do not create a release tag. Bad unuploaded artifact:
fix and generate a new candidate, then repeat all gates. Uncertain upload: query
actual PyPI versions, filenames and hashes first; never blindly retry.

For a published defect, stop recommending the version; the maintainer evaluates
yanking and a GitHub release warning. Security/trading risk takes priority: stop
affected operations, privately investigate, disclose a sanitized advisory and fix
forward with a unique Hotfix version. Never imply that rollback can cancel orders
or reverse funds movements. SDK auth state is in memory, with no SDK database
migration to undo; external broker state cannot be rolled back by package install.

There is currently no published P0-P3 known-good rollback target: 0.2.6 predates
those protections. Do not automatically downgrade to it and continue trading.
After a maintainer has verified and recorded a known-good version, the software
rollback command is (replace the placeholder with that approved version)::

    python -m pip install --force-reinstall 'emtl==KNOWN_GOOD_VERSION'

Until such a target exists, pause affected use and fix forward. A Hotfix branches
from an identified stable/master baseline, adds a minimal failing regression,
runs full required CI and artifact checks and receives a separate upload approval.
Do not delete/overwrite an immutable PyPI release. Record incident timeline,
affected versions, mitigation, fixed version and follow-up.

Maintenance ownership and triggers
----------------------------------

The repository maintainer owns monthly dependency review and immediate review on
an important security advisory. Dependabot may open PRs, never auto-merge. Preserve
current runtime pins; evaluate each change separately. requests/urllib3 updates
need request-count, redirect and exception regressions; OCR upgrades need approved
image fixtures. All updates need offline, package and HTML checks. Review CPython
3.11 / OCR migration by 2027-04-01 before Python 3.11 EOL; do not claim 3.12+ now.

Dependency inventory sources: setup.py (direct runtime), installed ``pip freeze``
and ``pip inspect`` (resolved transitive), pyproject.toml (build backend),
ci/requirements.txt and tox.ini (CI/test/check), docs/requirements.txt (Sphinx).
Record tool/resolved dependency versions per candidate. Review upstream security
advisories, Python limits and maintenance status; do not equate a frozen version
or successful tests with absence of vulnerabilities. Current runtime pins are
rsa==4.9, requests==2.33.1, ddddocr==1.4.11 and cryptography==50.0.2. The
previously identified Requests and cryptography advisories have targeted version
updates and final-master compatibility evidence; this is not a full SBOM or
zero-vulnerability guarantee. Dependabot PRs remain review-only; rsa 4.9 → 4.9.1
is pending separate review and must not be auto-merged.

The maintainer triages issues/PRs into security, trading risk, defect, compatibility,
installation, documentation, dependency or usage. Follow SECURITY.md for private
reporting; never request secrets publicly. Failed CI blocks release; retain failure
artifacts, reproduce with synthetic data and rerun at the final SHA. Publish only
accurate support claims. Maintain the current stable normally; old versions are
best effort, with no fixed SLA or unresourced long-term support promise. After each
release/incident, record elapsed time, failures, rollback/Hotfix, feedback and new
maintenance cost. Beta is opt-in and unsupported for production assurances.

Download the :download:`security policy <../SECURITY.md>` and the current
:download:`P4 dependency review <refactor/reports/P4-dependency-review.md>`.
