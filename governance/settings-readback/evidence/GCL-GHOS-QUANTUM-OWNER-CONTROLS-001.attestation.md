# GCL-GHOS-QUANTUM-OWNER-CONTROLS-EVIDENCE-001

## Evidence identity

- repository: `grandchallenge/QUANTUM-TECHNOLOGIES`;
- protected-main baseline: `260f469ba7349350c2b192a0e066a24aa670d611`;
- consolidated receipt SHA-256: `9eb34868b7f47759bf4210b4fc433c0942e602988a0b4bcd40745396bca6af04`;
- protected-main ruleset: `20106953`;
- immutable release-tag ruleset: `20355165`;
- CodeQL validation run: `30883403446`.

## Source evidence

The package preserves three exact owner-authenticated records:

- immutable release-tag receipt: `abb9380aa64387ae45c1078d9bc7612814c51a40968d7d204fc56ada50719067`;
- security-controls receipt: `318f527bfae3826f4b37cc7b50b1e28dbb89aaa43aead40ec40512a6606e7272`;
- protected-main readback: `eb7894acb4de2e63134d8c5684c7073a3e5670b0fa21194f4bd3bd6ae15dbba4`.

The first two receipts bind the API-transcribed tag and security stages. Issue
#21 comments `5174919919` and `5175015034` retain the owner-executed repository
merge-setting and protected-main ruleset stages. The final readback confirms
their current state and identifies ruleset `20106953`.

## Admitted target state

The evidence records:

- merge commits and squash merging enabled;
- rebase merging disabled;
- auto-merge and automatic merged-head deletion enabled;
- update-branch support disabled;
- an active default-branch ruleset prohibiting deletion and
  non-fast-forward updates;
- merge and squash as the only permitted merge methods;
- zero bootstrap approvals, stale-approval dismissal, and review-thread
  resolution;
- strict required contexts `validate`, `policy`, and
  `security / action-policy`;
- active immutable release tags with no bypass actors;
- vulnerability alerts and dependency graph, Dependabot security updates,
  and private vulnerability reporting enabled;
- CodeQL default setup for Actions and Python with extended queries, the
  remote threat model, the standard runner profile, and weekly scheduling;
- successful Actions and Python analysis jobs in run `30883403446`.

## Boundary

This package admits owner-control execution evidence only. It does not close
issues #21 or #14, dispose `QUANTUM-P1-001` or `QUANTUM-P2-001`, establish
repository or organization-wide conformance, certify mathematics, prove
quantum advantage, validate hardware, or authorize deployment,
manufacturing, product, or commercial claims. A separate post-repair
readback admission and standards-ledger overlay remain required.
