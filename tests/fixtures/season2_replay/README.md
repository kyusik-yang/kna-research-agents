# Season 2 replay fixtures

Inputs for tests/test_verdict.py, test_cards.py, test_prechecks.py, test_claim_sheet.py and
test_critic_calibration.py.

- `forum/`: copies of forum/073-090. Two lines differ from the originals. In 080 and 083 an
  absolute data path in a shell snippet is shortened to `.../kna/data/processed`.
- `doi_cache.json`: Crossref and OpenAlex answers for every DOI in those posts, fetched
  2026-09-25 through prechecks.resolve_doi, so tests never touch the network.
- `cards/R25.json` to `R30.json`: prediction cards built by hand from the Scout posts (073, 076,
  079, 082, 085, 088), in the v2.1 card format. Season 2 had no cards. Where a post stated no
  equivalence bound, the bound is the edge of the post's own support range. Gap quotes are
  verbatim abstract sentences from the DOI cache, and a side the post never quoted is marked
  `inferred` with no quote.
- `results/rNN/*.json`: one file per spec, with values transcribed from the Analyst posts (074,
  077, 080, 083, 086, 089). Each file names its source section. Sanity specs did not exist in
  Season 2 and are written as NOT COMPUTABLE.
- `timeline.json`: card commit, Analyst start and results times for the replay (set from the post
  dates, card first), the arc gates with the provenance recorded under D-10, and the headline
  claim assumed for each Critic verdict.
