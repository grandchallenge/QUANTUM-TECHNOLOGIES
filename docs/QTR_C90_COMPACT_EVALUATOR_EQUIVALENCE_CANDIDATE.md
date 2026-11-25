# C90 compact evaluator: exact storage-refinement candidate

**Status:** engineering candidate, not activation, independent certification, or campaign admission. The immutable scientific evaluator and all three compiled DAGs remain the authority. This proposal preserves the original source commit and adds a separate candidate and quality-blind tests only. Issue #114 governs execution.

## Identity

- Frozen evaluator source commit: `675865123437c3d6c908c7a3af337fd4023c5d0b`.
- Frozen evaluator Git blob: `92022fa89ceff9cf4ac0c9b6ce8613617664e1a6`.
- Candidate file: `reference/qtr_c90_native_eval_compact_refs_candidate.cpp`.
- Candidate SHA-256: `696cfc28bb6ef56993d84c31465d04ea041460ac5c7886df1a5b7f758e939a68`.
- Previously tested CHAD binary SHA-256: `e9c63b0d329e165cf96a1de37ee324f52ed35a95201dae347c4c6a4a3f35384c`. Compiler/host changes need their own build and execution identity; this digest is not assumed universal.

## Exact refinement argument

Scope: the three immutable valid C90 native DAGs, valid 49-bit selector coordinates, immutable backing files for the lifetime of each evaluation, and successful execution on a supported Linux mapping implementation. An allocation, mapping, arithmetic-overflow, I/O or custody error is not a successful result.

1. **Node reads.** The original and candidate use the same read-only private mapping, packed header/node layout, offset and memcpy. The candidate adds page-region tracking and MADV_DONTNEED, which discards resident mapping pages without altering the immutable underlying file. A later read faults those bytes back in. This preserves the read node, including a node crossing a region boundary, conditional on successful reads of the immutable file. The tracking target is not a proof of a hard RSS cap (kernel read-ahead and boundary faults may affect physical residency). Maintain measured host resource guards.
2. **Reference-count representation.** Decode the byte array and overflow map as r(i)=small[i] when small[i]<255, otherwise high[i]. The invariant is that high has exactly the keys with small[i]=255, and each stored count is at least 255. Initially and after clear the decoded map is identically zero. Increment below 254 adds one inline; increment at 254 inserts 255; increment above that adds one in high. Decrement below 255 subtracts one inline; decrement at 255 erases the key and writes 254; otherwise it subtracts one in high. Thus every valid count operation and read commutes with decoding. The original count type is uint32_t; each reachable node has at most two outgoing edge occurrences. All frozen DAGs have at most 249,840,004 nodes; 499,680,008 edge occurrences is below UINT32_MAX. Hence the original count cannot wrap on the frozen graphs; repeated child edges count twice in both implementations. For a failing/invalid input no equivalence of error messages is asserted.
3. **Reachability.** For a fixed selector, couple the original and candidate traversal states by equality of seen bits, pending stack, reachable count and decoded reference counts. Node reads, chosen selector branches, push/pop order, and binary edge occurrences agree. Induction over traversal gives the same reachable graph and counts.
4. **Evaluation.** At each ascending reachable-node step, couple slots, pool contents/free-list/live statistics, decoded counts, and already evaluated node values. The same node is read, operands selected identically, and the same unmodified integer arithmetic/min-plus code runs. Every consumed edge decrements the decoded count in the same way and releases the same slot exactly when its count becomes zero. The coupled invariant is preserved. The root value, reachable count, peak live count, release/reset behavior and JSON output fields are equal. This covers sum-product, soft-tropical and the min-plus primary representative and independent canonical key. The source delta introduces no changed arithmetic, selector order, graph, scoring or output formatter.
5. **Checkpoint.** The same header, selector binding, next-node index, reachable/peak statistics, ascending live-node order and values are written. On restore, identical reachability and prefix decrements produce identical decoded counts; live entries are reconstructed in the same order. Resume therefore preserves the coupled invariant, and the checkpoint bytes and completed output agree for a valid same-graph, same-selector checkpoint. This is not an authentication claim for arbitrary checkpoint bytes.

This is a storage-refinement argument for successful runs, not a proof of global runtime, RAM, OS or hardware equivalence. The original source is not replaced. The code-level argument should be independently reviewed against the exact candidate head and the real-graph differential evidence.

## Reproducible evidence

`python -m unittest discover -s tests -p test_qtr_c90_compact_refs_candidate.py -v` reconstructs the original from the pinned Git object, hashes both source identities, compiles the original and exact candidate plus a test-only forced-small-window variant, compares three algebras over 32 selectors each with an independent Python integer oracle, compares checkpoint bytes, tests all nine producer/consumer pairs per algebra and rejects incorrect bindings. 1,200 simultaneously live terms exercise shared references and counts above 255. The forced variant exercises eviction and boundary reads.

Real-graph engineering evidence (not decoder quality) is recorded in issue #114 comments 7148228575 and 7148636816: first-row byte matches for all three frozen graphs, concurrent two-worker execution, and a class-1 original differential; subsequent class-1 reference rows are retained separately. Graph sizes remain about 3.25 GB each; graph caching by algebra is operationally preferable. No private selector or outcome rows are published by this proposal.

## Remaining gate

The bounded class-1/batch-000 original differential is complete and its exact receipt reconciled. Protected review must decide whether this exact storage refinement can enter the existing execution route under issue #114; no provider dispatch, lowered scientific resource rule, candidate substitution, scoring, correction exposure, protected scientific promotion or campaign admission is implied by this proposal or green CI. The original frozen route remains available. Any activation must bind the exact candidate source/build, graph, selector, provider/lease, resource guard and original protected validator, not merely a descriptive name.
