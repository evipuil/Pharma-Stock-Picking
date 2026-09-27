# Versioning

StockPicking uses numbered Git tags and GitHub releases, matching the release
style used for the Academic Team and Research projects.

| Version | Meaning |
| --- | --- |
| `baseline_2026_08_19` / `v0.1` | Original frozen baseline at commit `2958acc` |
| `v1.0` | First numbered release of the current audited pipeline |
| `v1.1`, `v1.2`, ... | Subsequent documented updates |
| `v2.0` | A major change in methodology or project scope |

Tags identify exact commits and should remain unchanged after publication.
Package versions in `pyproject.toml` include the trailing patch component:
Git tag `v1.1` corresponds to package version `1.1.0`.

For each release:

1. Review the diff and exclude credentials, new bulk downloads, and local caches.
2. Run `python -m pytest -q` in the project environment. Record what was verified
   and whether empirical studies were rerun.
3. Update `pyproject.toml`, `README.md`, `CHANGELOG.md`, and a release note in
   `docs/releases/`.
4. Commit with a readable message such as `Version 1.1: improve catalyst coverage`.
5. Create an annotated tag, push the branch and tag, then create the matching
   GitHub release using the saved release note.

Example after committing the next release on `main`:

```powershell
git tag -a v1.1 -m "Version 1.1: improve catalyst coverage"
git push origin main
git push origin v1.1
```

Create the release from the repository's GitHub Releases page. Keep saved
historical results clearly separated from validation performed for a new release.
