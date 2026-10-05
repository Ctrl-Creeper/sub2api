# Release matrix

Fork automation and conflict notifications are documented in
[`../upstream-sync/README.md`](../upstream-sync/README.md). The release workflow
can also be called by `sync-upstream-release.yml`; managed tag-push runs are
skipped to avoid duplicate publication when the sync uses a PAT.

The release workflow builds the frontend once, then runs each configured Go target on its own Linux runner. `CGO_ENABLED=0` permits cross-compilation. The target matrix is read from `.goreleaser.yaml`, including its exclusions; simple releases select Linux amd64 only.

Each build uses GoReleaser OSS in snapshot mode with the selected release version and one target. Archive naming, bundled files, Go flags and release templates remain in the existing GoReleaser configurations. Every archive is accompanied by its source commit, target, version and SHA256. The publishing job verifies the complete matrix before building images or publishing. It uses GoReleaser's `extra_files` support to publish existing archives and checksums, with builds disabled. No Pro license is needed.

Go caches are isolated by target and refreshed on each source commit, with fallback to the preceding target cache. Save uses the original restore key, even if a build hook changes `go.sum`. Matrix jobs upload uniquely named artifacts. The publishing job extracts only the regular Linux binary from each verified archive and restores its executable permission before constructing Docker contexts. QEMU remains limited to runtime-image instructions. DockerHub images are omitted when its credentials are absent; GHCR is always retained. Simple mode still publishes only the amd64 GHCR image and the simple release description.

All build jobs use the commit resolved by `prepare`, including a manual release's selected tag. Helper scripts come from the workflow revision and are passed as a run-local artifact, so older application tags do not need to contain the new scripts. The workflow serializes release runs to prevent simultaneous updates to moving image tags.

## Version naming

Fork tags must be `v<upstream-version>-<positive-revision>`, such as `v0.2.13-1`.
The revision starts at 1 for each upstream release and increases for fork changes.
Bare upstream tags and zero/leading-zero revisions are rejected by the release plan.
Application versions, image tags and archive names omit only the leading `v`:
`0.2.13-1`, `ghcr.io/ctrl-creeper/sub2api:0.2.13-1`, and
`sub2api_0.2.13-1_linux_amd64.tar.gz`. Release titles use the BNDS brand.

Numeric fork revisions are **stable** releases despite SemVer's prerelease interpretation
of `-1`. The publisher explicitly sets the GitHub prerelease flag. An upstream
prerelease such as `v0.2.14-rc1` becomes `v0.2.14-rc1-1` and remains a prerelease;
its images do not replace `latest`, major or minor aliases. Source builds prefer exact
fork tags over upstream tags, falling back to `backend/cmd/server/VERSION`.

## Validate without publication

From a branch containing this workflow:

```bash
gh workflow run release.yml --ref <branch> \
  -f tag=<branch> -f dry_run=true -f simple_release=false
```

A dry run builds all selected archives and both runtime images, verifies artifact provenance and produces the final checksum file. It exports images locally as OCI archives instead of pushing them. It skips registry logins, GitHub Release publication, DockerHub description updates, Telegram notifications and VERSION synchronization. Test the simple path separately with `simple_release=true`.

Dry-run artifacts are available in the Actions run, including `release-dry-run-report`. Compare job start/end times, GoReleaser's build duration and cache restore results. Do not present an initial cold-cache run as a warmed-cache benchmark; publishing network time is not measured by dry runs.

Helper checks:

```bash
python -m pip install -r .github/release-tools/requirements-release.txt
python -m unittest discover -s .github/release-tools -p 'test_release_matrix.py'
bash -n .github/release-tools/release-images.sh
```
