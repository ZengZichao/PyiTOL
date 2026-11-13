# PyiTOL Release Runbook

English | [中文](RELEASE_CN.md)

This runbook covers the full "GitHub release + PyPI release" workflow. The current repository already has:
- an initial commit `c8220f1`, with releases published up to the latest tag `v1.0.3` (at that tag `setuptools_scm` derives version `1.0.3`; a working tree holding commits after it derives `1.0.4.devN+g…` instead);
- `.github/workflows/publish.yml`: pushing a `v*` tag automatically builds and publishes to PyPI (Trusted Publishing / OIDC, no token required);
- repository-wide links already point to the live repository `https://github.com/ZengZichao/PyiTOL`
  (owner `ZengZichao`, repository `PyiTOL`, as in `git remote -v`, `pyproject.toml`, `CITATION.cff`,
  `.zenodo.json`, `mkdocs.yml` and the READMEs), and `.github/workflows/publish.yml` documents the
  matching Trusted Publisher owner `ZengZichao`.

> WARNING: **the most important ordering principle** — `publish.yml` publishes to PyPI as soon as a `v*` tag is pushed. Therefore the **tag must be pushed only after every check passes**; never `git push --tags` at the very start.

---

## 0. Pre-release checks (must be completed)

### 0.1 Handle the `/discussions` link
If README / README_CN contain a `…/discussions` link, enable **Discussions** under the repository **Settings -> General -> Features**, otherwise it returns 404. If you do not want Discussions, simply delete that link.

### 0.2 Clean local build verification
```bash
rm -rf build dist src/pyitol.egg-info src/pyitol/_version.py
python -m build
twine check dist/*        # validate sdist / wheel metadata
```
If `twine` / `build` are not installed: `pip install build twine`.

---

## 1. Path A: private verification -> make public (recommended)

### 1.1 Create a **private** repository on GitHub
- Repository name `PyiTOL` (the name every link in this repository uses; the PyPI distribution name remains the lowercase `pyitol`); do **not** check "Initialize with README / .gitignore / License" (the local history is already complete).
- Note the repository URL: `https://github.com/ZengZichao/PyiTOL.git`

### 1.2 Push `main` (do **not** push tags yet)
```bash
git branch -M main
git remote add origin https://github.com/ZengZichao/PyiTOL.git
git push -u origin main          # push only main, not the tags
```

### 1.3 Verify while still private
- Open the repository **Actions** page and confirm CI (`ci.yml`) passes.
- Run the local functional self-check:
  ```bash
  pip install -e ".[dev]"
  pyitol self-test
  pytest tests/ -m "not integration"
  ```
- At this point the repository is still Private and invisible to others, so you can safely inspect the code, secrets, and logs.

### 1.4 Configure the Trusted Publisher on PyPI (one-time)
1. Register / log in at https://pypi.org
2. **Account settings -> Publishing -> Add a new trusted publisher**:
   - PyPI project name: `pyitol`
   - Owner: `ZengZichao` (exactly as recorded in the prerequisite comment of `.github/workflows/publish.yml`)
   - Repository name: `pyitol`, also verbatim from that comment (the GitHub repository itself is named `PyiTOL` — if you ever change the name or casing, update `publish.yml` and this list together)
   - Workflow name: `publish.yml`
   - Environment name: leave blank or set to `pypi`
3. Save. **The repository can publish even while Private**, since the Trusted Publisher does not depend on visibility — so before step 1.5 flips it to public, as long as you do not push a tag, nothing is accidentally published.

### 1.5 Switch to public
Repository **Settings -> General -> Danger Zone -> Change repository visibility -> Make public**.
The history, existing tags, and the current version `v1.0.3` are all preserved, with zero migration.

### 1.6 Final release (last step: push the tag)
```bash
git push origin --tags        # push v* tag -> triggers publish.yml -> publishes to PyPI
```
- Watch the **Actions** page to see whether `Publish to PyPI` succeeds.
- `publish.yml` only builds and publishes to PyPI — **nothing in CI creates a GitHub Release**, and pushing a tag does not create one either. If you want a Release (Zenodo requires one), create it explicitly with `gh release create`, as shown in 4.2.

---

## 2. TestPyPI dry run (strongly recommended once before a real release)

PyPI has no "private" concept, but you can use **TestPyPI** (`test.pypi.org`) to rehearse the release and confirm the sdist/wheel upload and metadata are correct.

```bash
# 1) Register a TestPyPI account and generate an API token (Account settings -> API tokens)
# 2) Build locally and upload to TestPyPI
rm -rf build dist
python -m build
twine upload --repository testpypi dist/*     # Enter TestPyPI username(__token__)/password(token) when prompted
```
- The dry run validates the "packaging + upload" path; the real release still goes through the GitHub Actions in 1.6 (Trusted Publishing).
- Optional: you can also configure a Trusted Publisher in the TestPyPI console and rehearse via Actions with `git tag -a v0.0.0-test ...`, but local `twine` is simpler.

---

## 3. Post-release verification

- PyPI page: https://pypi.org/project/pyitol/ should show the current version `1.0.3`.
- Install verification:
  ```bash
  python -m venv /tmp/verify
  /tmp/verify/bin/pip install pyitol
  /tmp/verify/bin/pyitol --help
  ```
- GitHub Release page: `https://github.com/ZengZichao/PyiTOL/releases` shows the corresponding tag (e.g. `v1.0.3`) — but only if you created the Release yourself (see 1.6 and 4.2); it does not appear just because the tag was pushed.

---

## 4. Zenodo DOI (paper citation)

### 4.1 One-time setup (web console)
1. Log in at https://zenodo.org (logging in with your GitHub account is recommended).
2. **Settings -> GitHub -> Connect GitHub account** (or "Sync now") to sync your repository list.
3. Find `ZengZichao/PyiTOL` and flip the **Enable** switch on.
4. The repository root already contains `.zenodo.json` (title / authors / ORCID / license / keywords, read automatically by Zenodo when archiving), so no extra configuration is needed.

### 4.2 Triggering and verification
- Each time a GitHub **Release** is published, Zenodo automatically captures a repository snapshot and mints a DOI (within about one minute; visible on the Zenodo record page).
- WARNING: Zenodo responds only to a **Release**, not to a tag push. Pushing a tag on GitHub does not automatically create a Release, so create one explicitly:
  ```bash
  gh release create v1.0.3 --generate-notes
  ```
- WARNING: the hook must be **enabled before the Release is created**, otherwise that Release will not be archived automatically.
- Query the DOI:
  ```bash
  curl -s "https://zenodo.org/api/records?q=pyitol" | jq '.hits.hits[].doi'
  ```

### 4.3 DOI semantics
- **Version DOI** (one per Release): `10.5281/zenodo.<id>`, pointing to that specific snapshot.
- **Concept DOI** (the whole software series, version-independent): `10.5281/zenodo.<conceptid>`, always resolving to the latest version.
- v1.0.0 first release: version DOI `10.5281/zenodo.22043046`, concept DOI `10.5281/zenodo.22043045`.
- v1.0.1 record: version DOI `10.5281/zenodo.22046669` (a metadata fix patch; code logic identical to v1.0.0).
- v1.0.2 record: version DOI `10.5281/zenodo.22056427` (reran all benchmarks B1–B5 with an embedded `_provenance` version stamp; fixed the key resolution and zip tree-filename issues in the B4 diagnostic re-post).
- v1.0.3 record: version DOI `10.5281/zenodo.22106806` (duplicate-label hard error in the validator, POST-retry warning in the API client, and an extra 50,000-leaf data point in the archived template scalability results, generated with `--sizes` since the benchmark's default sizes are 100 / 1,000 / 10,000; commit `b9a1207`).
- **Citation decision**: the Bioinformatics submission cites the **latest version DOI** (`10.5281/zenodo.22106806`, v1.0.3; abstract and reference [34]); general citations may use the concept DOI.

---

## 5. Troubleshooting / rollback

- **Published the wrong version**: PyPI does not allow overwriting the same version number, so you can only publish a new `patch` version (e.g. `v1.0.4`). A release can be deleted, but deleted files can never be re-uploaded or restored, so **always rehearse before releasing**.
- **publish.yml fails**: inspect the Actions log for the cause. A common reason is that the Trusted Publisher's owner/repo/workflow do not match — recheck 1.4.
- **Wrong version number (e.g. `0.2.3.dev0` appears)**: this means `setuptools_scm` did not pick up a tag. Confirm `git push origin --tags` ran and that the Actions checkout uses `fetch-depth: 0` (already configured in publish.yml).
- **Want to re-publish the same version**: delete the old local and remote tag, then re-tag:
  ```bash
  git tag -d v1.0.3 && git push origin :refs/tags/v1.0.3
  git tag -a v1.0.3 -m "Release v1.0.3" && git push origin v1.0.3
  ```

---

## Appendix: alternative Path B (mirror to a public repository)

If you would rather first validate the code in a separate independent private repository and then migrate everything wholesale (instead of changing visibility), use `git push --mirror` to carry branches and tags in one shot (**never "Download ZIP"**, which drops the `.git` history and tags and scrambles the version number):

```bash
git remote add public https://github.com/ZengZichao/PyiTOL.git
git push --mirror public
```
Afterwards, still run 1.4 (register the public repository as the Trusted Publisher) -> 1.6 to trigger the release.

> Path A (change visibility) is less effort and involves no migration; it is the recommended default.
