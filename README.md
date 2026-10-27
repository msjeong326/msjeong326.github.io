# Minsoo Jeong — academic website

English: https://msjeong326.github.io/

한국어: https://msjeong326.github.io/ko/

Static bilingual academic website, hosted by GitHub Pages from the root of
the `master` branch. `.nojekyll` keeps the existing HTML and asset paths intact.

Current appointment: Visiting Scholar, Department of Plant Sciences,
University of California, Davis, Melotto Lab. Sejong Science Fellow and
Postdoctoral Researcher, Kyungpook National University.

The publication inventory was checked against publisher-deposited DOI metadata
on October 27, 2026. It contains 35 published or publicly available online
articles. Future issue dates and early online versions retain their labels.
Co-first authorship and corresponding authorship are separate roles.

`data/publications.json` is the shared public inventory. After verifying a new
record with its publisher, update that file, the update date, and any headline
counts or appointment details that have changed. Then regenerate both pages:

```bash
python3 scripts/render_publications.py
python3 scripts/render_publications.py --check
```

The renderer uses only the Python standard library. It updates the marked
publication regions while preserving the rest of each page. Both languages
serve complete publication HTML without requiring JavaScript; JavaScript adds
role filters and expansion controls.

Before publishing, check both languages at desktop and phone widths, the
publication filters, expanded list, email links, navigation and image assets.
Commit only selected public website files. Local management records, archives,
original CVs and administrative documents do not belong in this repository's
public commits.
