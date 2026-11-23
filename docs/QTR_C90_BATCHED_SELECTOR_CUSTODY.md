# C90 native selector batching: controlled transport

## Scope and authority

This changes **only** the external execution transport for the frozen
QTR-C90-EXACT-DECODER-001 operation, under issue #114 and its Council
pre-outcome freeze. It does not change the scientific evaluator, selector
generation, the 347-input corpus, compile identities, canonical order, exact
arithmetic, C72 decoder, scoring or matched comparison.

The original evaluator accepts any nonempty ordered selector file and clears
its live value state between selectors. Each original work unit is an
`(algebra, logical_class)` pair; there are **3 × 256 = 768** units. The
transport partitions an **individual** 347-selector unit into 22 batches:
21 × 16 plus a final 11. No frozen selector is omitted or duplicated.

## Workflow on the existing externally governed CPU provider

Prepare the exact frozen input list using the pinned activation's
`reference/qtr_c90_exact_native_campaign_001.py selectors`. Verify that the
checkout is the execution source commit
`675865123437c3d6c908c7a3af337fd4023c5d0b`, all scientific blobs match,
the compiled graph has the digest specified by the frozen activation, and
the evaluator was compiled from that source.

Keep **two separate source checkouts**. The scientific source stays pinned to
`675865123437c3d6c908c7a3af337fd4023c5d0b`; the transport program is
read from a protected-main checkout that includes PR #139. Do not copy the
new transport script into the frozen scientific source or move that source's
HEAD.

```bash
FROZEN_SOURCE=/path/to/frozen-execution-checkout
QTR_MAIN=/path/to/protected-main-checkout
ORIGINAL_NATIVE_EVAL=/path/to/original-frozen-evaluator
FROZEN_GRAPH=/path/to/frozen-compiled-graph.qtrbin
WORK=/path/to/provider-owned-work-unit
mkdir -p "$WORK"

test "$(git -C "$FROZEN_SOURCE" rev-parse HEAD)" = \
  675865123437c3d6c908c7a3af337fd4023c5d0b
test -f "$QTR_MAIN/scripts/qtr_c90_selector_batches.py"
BATCH_TOOL="$QTR_MAIN/scripts/qtr_c90_selector_batches.py"
cd "$FROZEN_SOURCE"  # frozen adapter verifies its own Git identity

python3 "$FROZEN_SOURCE/reference/qtr_c90_exact_native_campaign_001.py" \
  selectors --logical-class 17 --output "$WORK/selectors.txt"
python3 "$BATCH_TOOL" plan "$WORK/selectors.txt" "$WORK/class-17" \
  --algebra soft_tropical_base_2 --logical-class 17 --size 16
```

Use the **original frozen** native executable for each batch:

```bash
"$ORIGINAL_NATIVE_EVAL" --native "$FROZEN_GRAPH" \
  --selectors "$WORK/class-17/batch-000.selectors.txt" \
  > "$WORK/class-17/batch-000.rows.jsonl"
python3 "$BATCH_TOOL" verify "$WORK/class-17" 0 \
  --evaluator "$ORIGINAL_NATIVE_EVAL" --graph "$FROZEN_GRAPH"
```

Repeat for batches 001–021. Verify each process exits zero and preserve its
GNU-time receipt; atomically return each verified batch's inputs, rows,
receipt and resource log to CHAD, then independently rehash and inspect it.
**Do not confuse a local receipt with independent external attestation.**

Only reuse an already completed batch after validating its source, graph,
evaluator, input and output digests and its custody receipt. Reject
unverified partial rows, stale provider identity, missing batches, duplicate
indices, wrong classes, corrupted metadata or altered scientific identities.

Once all 22 batch receipts are present:

```bash
python3 "$BATCH_TOOL" join "$WORK/class-17" "$WORK/complete-class-17.jsonl"
python3 "$FROZEN_SOURCE/reference/qtr_c90_exact_native_campaign_001.py" \
  validate-shard --algebra soft_tropical_base_2 --logical-class 17 \
  --rows "$WORK/complete-class-17.jsonl" --output "$WORK/class-17-semantic-receipt.json"
```

The frozen **347-row semantic validator** is mandatory. A completed class
may enter bounded engineering custody only after its exact source/compile
identities, all batch receipts and semantic validation are reviewed. It does
not establish decoding quality or authorize mathematical certification.
**No C90 result scoring or matched comparison** occurs until the complete
three-algebra, 256-class domain is fixed and independently scored according
to issue #114.

## Recoverability and compute placement

Per-batch return and verification limits interrupted work loss to the
currently unverified chunk. The official class-0 soft-tropical replay on
CHAD established full 347-row native equality with the retained candidate
and passed frozen semantic validation. These results do not imply universal
arithmetic equivalence, speed superiority or complete campaign outcomes.

Per AGENTS.md, route substantial subsequent work to the **existing Colab
high-RAM CPU runner first**; if unavailable, select only a governed compatible
external-provider fallback. CHAD is the control and validation host, not the
default bulk executor. Provision against actual 7 GiB/worker plus reserve
requirements, provider lease, durable checkpoint transfer and compute balance.
Never dispatch another large campaign without resources and a lease adequate
for checkpoints. Use the existing repository execution profile and job
envelopes; do not start a second queue or supervisor.

## Recovery and rollback

Keep completed verified receipts immutable and retain the original source.
On interruption, reconcile the exact provider session and completed batch
digests, then resume only genuinely missing batches. Do not overwrite a
partial or ambiguous batch without forensic examination. The fallback is
the prior original full-347 evaluator invocation; remove the batching
transport without changing any scientific input, frozen checksum or outcome.

## Remaining-domain projection after class-0 admission

Protected PR #139 admits class-0 original-native engineering shards for all
three algebras: 3 of 768 units. The existing batch transport now provides
a deterministic projection of the other 765 units, not a second queue,
provider lease, scientific authority or scheduling daemon.

In a protected-main transport checkout, after reconciling current GitHub
admissions and before selecting provider work, run the existing
scripts/qtr_c90_selector_batches.py campaign-plan command, with output
WORK/remaining-c90-batches.json and --protected-head bound to the exact
current transport checkout HEAD. Keep the frozen scientific checkout separate.

The immutable projection checks the SHA256 of protected class-0 admission
evidence and binds all three prior class-0 row identities. It enumerates
765 pending work-unit IDs and their algebra, logical class, frozen graph,
347-selector cardinality and 22-batch transport shape. Total pending
computational work: 265,455 selectors across 16,830 batches.
This derived index contains no outcome values and does not authorize execution,
scoring, matched comparison, certification or scientific promotion.

For any chosen unit, use the original-native plan, verify, join and frozen
validate-shard sequence specified above. Before rerunning after new admission,
reconcile current protected GitHub results, regenerate the derived index,
and reject stale provider leases. The existing GCL external execution
profile remains the governing provider/work-unit contract.

No bulk work may start merely because this projection exists. Resource
and lease preflight, external provider authorization, incremental
custody transfer and independent readback remain mandatory. Colab
high-RAM CPU is default per AGENTS.md; external fallback is governed.
