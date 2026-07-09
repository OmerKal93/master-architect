# Release process

`agent-lint` is released via GitHub's tag-triggered `.github/workflows/release.yml`, publishing
to PyPI through [trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) — no API
tokens are stored in this repository. This is deliberately minimal machinery
(`EXECUTION.md`'s deferred-architecture ledger: "full release machinery... arrives when release
cadence becomes painful"); there is no automated changelog generation or version-bump tooling
yet — both are manual, documented steps below.

## One-time setup (a human with PyPI account access must do this)

1. Confirm the project name `agent-lint` is available on PyPI (checked and recorded in
   `docs/DECISIONS.md` — fallback `art-lint` if it's been claimed since).
2. Create the `agent-lint` project on PyPI (the first publish can also create it, if trusted
   publishing is configured as a "pending publisher" — see PyPI's docs linked above).
3. On the project's PyPI settings, add a trusted publisher: GitHub owner `OmerKal93`, repository
   `master-architect`, workflow `release.yml`, environment `pypi`.
4. In this GitHub repository's settings, create an environment named `pypi` (Settings →
   Environments). Optionally add required reviewers for extra safety on the publish step.

Until this is done, `.github/workflows/release.yml` exists but will fail at the publish step if
triggered — nothing can be silently published without this explicit, human-completed step.

## Cutting a release

1. Ensure `main` is green (CI passing) and `CHANGELOG.md`'s `[Unreleased]` section accurately
   describes everything since the last release.
2. Bump the version in `packages/agent-lint/pyproject.toml` (`[project] version = "X.Y.Z"`).
3. Move the `[Unreleased]` section in `CHANGELOG.md` to a new `## [X.Y.Z] - YYYY-MM-DD` section;
   leave a fresh empty `[Unreleased]` above it.
4. Commit: `chore(release): vX.Y.Z`.
5. Tag: `git tag vX.Y.Z` and `git push origin vX.Y.Z`. This triggers the release workflow.
6. Verify the package on PyPI, then verify a clean install: `pip install agent-lint==X.Y.Z` in
   a fresh environment, followed by the quickstart demo (`docs/quickstart.md`).
7. If something is wrong post-publish: PyPI does not allow re-uploading the same version.
   [Yank](https://packaging.python.org/en/latest/guides/making-a-pypi-release/#uploading-your-package-to-pypi)
   the bad release on PyPI (marks it as "don't install by default" without deleting it) and cut
   a new patch version with the fix.

## Versioning

Pre-1.0: any release may include breaking changes, documented in `CHANGELOG.md` and (for
anything affecting the plugin/rule-author contracts) called out explicitly. There is no separate
long-term-support branch — see `PLAN.md` section 28 for the full post-1.0 policy this will
graduate to.
