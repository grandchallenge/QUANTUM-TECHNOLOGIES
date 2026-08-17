# QTR-TCM-QDEC-COMPARE-001 — bounded shared-interface conventional decoder comparison

## Status

Scientific candidate only. The immutable scientific registry and evidence remain
`candidate_executable_not_promoted`. No comparison promotion authority and no
`QEC-CIRCUIT-001` authority exists at this stage.

Human Steward authorization: issue #70 comment `5320400759`,
`ADOPT_WITH_AMENDMENTS__AUTHORIZE_TCM_QDEC_COMPARE_001_ONLY`.

Council Referee recommendation: issue #70 comment `5320307737`,
`RECOMMEND_ADOPTION_WITH_AMENDMENTS__NO_EXECUTION_AUTHORITY`.

Execution docket: #71.

Protected starting main:
`d2cef907ee3c1ae1d56f0625c706a87d35b3c89f`.

Canonical pre-measurement manifest first commit:
`a187bcbd52d032ab62c85d5aa9c4e5d44576b45b`.

Manifest payload:
`c68830f40733cde6957713060cec35adf317c75572cc960610c07c4d0e24d1e2`.

Candidate committed evidence payload:
`9bd93dd1f0b6c5d7ca59523c7dfd382524639adf77aefaedd8900b2b01de6b7c`.

Full exact bootstrap report payload bound by that evidence:
`6385c2da742e14ecf2bc41336c78c2a8ff42b1cdd897fb5e7cfac056e2214146`.

## Scientific question

Under one frozen one-sector code-capacity decoding interface, exact independent
correctness oracle, precommitted input corpus, and source/configuration-pinned
conventional implementations, what comparison statements are actually defined
between the promoted TCM semantics and conventional BP/min-sum/BP-OSD methods?

The comparison relation is deliberately partial. A decoder-quality statement is
admissible only when both methods return correction-valued outputs on the same
protected input cell. A missing, interface-uncertified, or resource-not-reached
TCM cell cannot be turned into a quality ranking.

## Pre-measurement lock

The comparison manifest was committed before the first measured decoder input.
It binds:

- the promoted `QLDPC-SCALE-001B` predecessor identities;
- C18, C72, and C90 as the only authorized surfaces;
- all corpus definitions and digests;
- the X-error one-sector syndrome/correctness convention;
- exact historical package/source identities;
- the three conventional rows and their configuration;
- maximum BP iterations and no-retry rule;
- method-native counter semantics;
- typed missing-cell semantics;
- the downstream exclusions.

No decoder parameter, corpus member, channel prior, iteration cap, OSD order, or
comparison rule was selected after outcomes were observed.

## Historical conventional implementation lock

The execution uses the historical compatibility target already recorded by the
programme:

- `ldpc==0.1.53`;
- PyPI source distribution SHA-256
  `3b2652aa993ab71672d680ac76ee2dcf3dc289fc5d11c07d060e5f838d8c3601`;
- exact upstream `quantumgizmos/ldpc` commit
  `8e2cba3206cf639518164d8b409f7d21b17d0738`;
- `bp_decoder.pyx` blob `dbee68689c795bc2417166e2e25eb495fa4be5bb`;
- `osd.pyx` blob `1e588ab70dbc684f45f36bbdeed524d0c98b70d0`;
- `bposd==1.6` wheel SHA-256
  `80e439246c11ca824610f9bc7858c68eb1f8a6b7cbb71760cf6c86e03c47ff5d`.

The exact rows are:

- `BP_MIN_SUM`: standalone pure `ldpc.bp_decoder`, `bp_method="ms"`,
  `max_iter=10000`, scaling factor `0`, no OSD class/path;
- `BP_OSD_CS_7`: `ldpc.bposd_decoder`, min-sum BP, `max_iter=10000`,
  scaling factor `0`, `osd_cs`, order `7`;
- `BP_SUM_PRODUCT`: standalone pure `ldpc.bp_decoder`, `bp_method="ps"`,
  `max_iter=10000`, no OSD class/path.

The packages are downloaded from their exact PyPI release records, SHA-256
verified before installation, and version-checked after installation.

## Shared code-capacity interface

This work package studies one X-error CSS sector only.

For injected physical error `e`:

- syndrome is `s = H_Z e` over GF(2);
- a conventional decoder receives `H_Z`, `s`, and constant BSC `p=0.1`
  channel metadata;
- returned correction `c` is syndrome-consistent iff `H_Z c = H_Z e`;
- exact success is decided independently iff `e XOR c` is in
  `rowspace(H_X)`.

Decoder convergence flags are metadata, not the correctness oracle.

The larger-code scorer tests row-space membership by deterministic GF(2) basis
reduction rather than enumerating the stabilizer span. The preflight test proves
this implementation exactly equivalent to explicit stabilizer-span membership
for every one of the `2^18` ambient C18 vectors.

## Surface C18 — matched head-to-head calibration

C18 is the already-promoted `[[18,4,4]]` Fixture 002 one-sector corpus:
all `4048` errors of Hamming weight `0..4`, corpus digest
`260b1a43cf1d777f28c475918e91a5f7cefc5d28a2bfb556338f7e30058f58a8`.

Protected TCM decision rows are replayed without changing their semantics:

- sum-product BSC `p=0.1`: `263/4048` successes;
- soft-tropical base 2: `262/4048`;
- min-plus deterministic default: `226/4048`, with certified tie envelope
  `[218,263]`.

Conventional exact-oracle totals on the same 4048 inputs are:

- `BP_MIN_SUM`: `145/4048`;
- `BP_OSD_CS_7`: `244/4048`;
- `BP_SUM_PRODUCT`: `19/4048`.

These totals are not a family-level leaderboard. They are finite C18 facts.
The exact matched pairwise comparison preserves non-dominance information:

- BP-OSD versus TCM sum-product: `244` versus `263`; BP-only successes `178`,
  TCM-only successes `197`;
- BP-OSD versus TCM soft-tropical: `244` versus `262`; BP-only `179`,
  TCM-only `197`;
- BP-OSD versus deterministic min-plus: `244` versus `226`; BP-only `191`,
  TCM-only `173`.

The last row must not be rewritten as unconditional BP-OSD superiority over
min-plus: the protected min-plus decision is tie-sensitive and its certified
success envelope is `[218,263]`.

Similarly, the protected exact coset-leader lookup (`240`) and greedy baseline
(`125`) remain historical reference anchors only. This comparison does not
retroactively claim that any TCM row generally “beats exact lookup”.

## Surface C72 — conventional reach/status only

The precommitted C72 corpus contains `329` inputs:
zero, every unit error, and 256 deterministic SHA-derived BSC `p=0.1` errors.
Digest:
`23b49e39eafd70c9619f8837dfcb0046e13a1600cd7176d42a6018814f518050`.

The TCM cell remains exactly:
`SHARED_DECODER_INTERFACE_NOT_CERTIFIED`.

The conventional rows complete on this frozen sample:

- `BP_MIN_SUM`: exact oracle success `161/329`;
- `BP_OSD_CS_7`: `161/329`;
- `BP_SUM_PRODUCT`: `144/329`.

These are bounded conventional sample facts only. No TCM quality comparison is
defined on C72.

## Surface C90 — first TCM compilation-boundary reach/status surface

The precommitted C90 corpus contains `347` inputs under the same deterministic
rule. Digest:
`b053a27a9c346832d6008987e204c88162dc1797e0367b38705861049059e086`.

The TCM cell remains frozen from promoted 001B as:
`NOT_REACHED_EXACT_COMPILATION_BOUND`.

The conventional rows complete on this frozen sample:

- `BP_MIN_SUM`: exact oracle success `200/347`;
- `BP_OSD_CS_7`: `211/347`;
- `BP_SUM_PRODUCT`: `171/347`.

This establishes only conventional execution/reach on this protected C90
sample while the inherited exact TCM path was not reached under its frozen
compilation envelope. It does not establish `BP > TCM`, conventional
scalability, or TCM non-scalability.

## Deterministic accounting

The evidence retains exact method-native fields including:

- BP convergence/non-convergence counts;
- BP iterations performed;
- syndrome-consistency counts;
- OSD invocation counts;
- source-derived nominal OSD candidate counts where applicable;
- correction weights;
- exact result-record digests.

No synthetic universal operation count is constructed across unlike methods.
Wall-clock, RSS, allocator, throughput, and accelerator measurements are not
part of the authoritative evidence.

## Operational repair history

Two monolithic bootstrap attempts were terminated by the hosted runner with
exit `143` after all manifest/package gates passed. They were recorded as
`OPERATIONAL_EXECUTION_INCOMPLETE`, not decoder evidence.

An initial cell-sharded run exposed an evaluator implementation error on larger
codes: the scorer attempted to materialize the complete stabilizer row span,
which is exponential in stabilizer rank. No completed larger-cell scientific
output was admitted from that path.

The oracle implementation was then replaced by exact GF(2) basis reduction.
An exhaustive C18 ambient-space test certifies that the old explicit-span
predicate and the new basis-reduction predicate agree on all `262144` vectors.
The scientific definition of correctness did not change.

The final bootstrap execution uses a deterministic 3-surfaces × 3-method cell
shard, with one decoder invocation per frozen input and no retry. All nine cells
completed and were assembled deterministically.

## Candidate adjudication

Primary candidate outcome:

`SHARED_INTERFACE_COMPARISON_COMPLETED_ON_C18`

Secondary candidate outcomes:

- `TCM_SHARED_DECODER_INTERFACE_NOT_CERTIFIED_ON_C72`;
- `CONVENTIONAL_BASELINES_REACHED_C90__TCM_NOT_REACHED_EXACT_BOUND`.

These are candidate scientific findings only until exact-head review and any
separate promotion overlay are completed.

## Fail-closed claim boundary

This work package does not certify or authorize:

- a general `TCM > BP`, `BP > TCM`, or BP-OSD superiority theorem;
- a decoder-family leaderboard;
- quality comparison against TCM on C72 or C90;
- asymptotic/family decoder scaling;
- practical runtime or memory superiority;
- hyperparameter search or post-outcome tuning;
- approximate TCM;
- circuit-level or repeated-syndrome decoding;
- measurement-error or phenomenological noise;
- thresholds or pseudo-thresholds;
- hardware validation;
- learned decoding;
- adaptive online TCM ordering;
- `QEC-CIRCUIT-001`;
- `QLDPC-FORGE`;
- autonomous code, decoder, circuit, or architecture search.

Any later circuit-level referral is a separate governance decision.
