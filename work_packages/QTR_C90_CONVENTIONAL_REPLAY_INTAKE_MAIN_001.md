# QTR-C90 conventional replay — protected-main evidence intake

Status: \`OCTOBER_REPLAY_CONTENT_EQUIVALENCE_VERIFIED__NO_NEW_DECODER_SCORING\`

Recorded: 2026-11-20. Scope: only the previously established conventional C90 baselines, **not** the incomplete exact C90 decoder campaign.

## Problem and preserved provenance

The original promoted conventional comparison ZIP is no longer available:

- Original run **32079738866**, artifact **9304727792**, exact head \`3ebe409c60e7907b8251d44ee822141159d2879c\`, original ZIP SHA-256 \`34f37ec1a351a42e08c7143b359ca40191db4cd92ceeab2881930a67e3942182\`.
- It is **not** claimed that the original ZIP bytes, original execution receipt or original working directory were recovered.

A genuine later replay does remain available:

- October run **40511661627**, artifact **12738710046**, actual replay head \`c588cbbc635fe477c8496fd69e6145f62b768b2e\`, ZIP SHA-256 \`dd59ab416d41b1e9025d82319e28bd0ab622e0cdc6e10b097ca470a879dd3a46\`.
- Frozen original scientific reference source \`675865123437c3d6c908c7a3af337fd4023c5d0b\`. This verifier transcribes frozen evidence commitments but neither imports nor changes that unmerged science branch.
- C90 frozen input corpus SHA-256 \`b053a27a9c346832d6008987e204c88162dc1797e0367b38705861049059e086\`.
- Full private replay report canonical SHA-256 \`6385c2da742e14ecf2bc41336c78c2a8ff42b1cdd897fb5e7cfac056e2214146\`.

The public protected report \`evidence/TCM-QDEC-COMPARE-001-report.json\` is a *narrower, promoted projection* of the complete report. Its canonical self-hash is \`9bd93dd1f0b6c5d7ca59523c7dfd382524639adf77aefaedd8900b2b01de6b7c\`, and its \`full_report_payload_sha256\` binds the complete source report. The verifier checks **both** self-hashes, the full-report pointer, and every field preserved by the public projection; it must not falsely require identical JSON objects or overwrite one provenance with the other.

## Exact conventional outcome commitments

| Existing method | Frozen successes / 347 | Per-input outcome-vector SHA-256 |
|---|---:|---|
| BP_MIN_SUM | 200 | \`9652133baf36b83605c2f394067bd25938b47eb9595435b72470256ca1fe5bae\` |
| BP_OSD_CS_7 | 211 | \`bd2141809336ae41db0a5e471be74603e780f6b7beba72a541bdc00132ab50ea\` |
| BP_SUM_PRODUCT | 171 | \`d943dcfbf110e8c1e57558bddec270da374d6ea0abc9be9923d848e30eac3f48\` |

Each outcome vector contains exactly **347 Boolean entries**. Its canonical SHA-256, original cell payload digest, detailed-result-record digest and totals must all agree with the frozen source *and* the full report. These are **pre-existing conventional** benchmark results. The new C90 exact decoder remains unscored.

## Implemented and tested clean protected-main route

\`scripts/qtr_c90_conventional_replay_intake_001.py\` is an independent, standard-library-only Python intake checker. It does not import the unmerged reference decoder or promote the historical PR #129 branch.

\`\`\`bash
python3 scripts/qtr_c90_conventional_replay_intake_001.py \
  --archive /private/pinned/12738710046.zip \
  --protected-report evidence/TCM-QDEC-COMPARE-001-report.json \
  --check-github-metadata
\`\`\`

The \`--check-github-metadata\` option performs an authenticated GitHub API identity readback. The private ZIP is **not committed** to this repository; these are instructions for an authorized operator with the original bytes.

Adversarial controls in \`tests/test_qtr_c90_replay_intake_001.py\` include one synthetic valid replay, rehashed wrong replay head, rehashed altered conventional outcome vector, independently rehashed wrong public report projection, a corrupt ZIP, and an opt-in actual 2026-10 replay ZIP check. **All six** passed on CHAD with the authenticated real ZIP and the current protected report. The real archive check is skipped in generic CI if those authorized private files are not mounted.

## Boundaries

- **This PR never computes, fixes or scores a C90 exact decoder correction.**
- Existing frozen \`reference/\` files, quality-blind class-shard receipts, and the original external C90 runner are unchanged.
- The missing August ZIP is **not** byte-verified; the October artifact retains its true separate run, head and ZIP identity.
- The source-locked C90 exact campaign still requires 768 complete class/algebra shards, all corrections fixed under quality blindness, then only afterward independent score and nine matched comparisons. Two external shards were independently verified by 2026-11-20. The third algebra is a separate ongoing calibration.
- The scoring adapter in historical [PR #129](https://github.com/grandchallenge/QUANTUM-TECHNOLOGIES/pull/129) is not imported onto protected main. Its historical execution branch has incompatible routing policies; an eventual scientific scoring integration requires a separately reviewed executable route **after** all corrections are fixed.
- Publication certification, speed superiority, scientific novelty and Paper B are not claimed.

This change is intended for **protected admission of baseline evidence integrity**, not protected admission of the incomplete C90 scientific campaign.
