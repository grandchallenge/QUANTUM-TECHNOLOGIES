# QTR-NOVELTY-UTILITY-AUDIT-001

Status: `WORKING_PRIOR_ART_AUDIT__NO_NOVELTY_CERTIFICATION`

Audit date: 2026-10-02

Programme: `GCL Quantum Technologies Research (QTR)`

Repository: `grandchallenge/QUANTUM-TECHNOLOGIES`

Publication branch: `publication/qtr-exact-inference-001`

## 1. Purpose

This audit separates three questions that must not be conflated:

1. whether a QTR result is scientifically useful;
2. whether the mechanism is technically differentiated from prior work;
3. whether a defensible publication novelty claim can be made.

The audit is deliberately conservative. Failure to find prior art is not proof of priority. No claim of “first”, “novel”, or “state of the art” is authorized by this document.

## 2. Bottom-line finding

The QTR workset contains substantial scientific utility and several potentially publishable contributions, but the strongest publication case is narrower than the full programme.

The broad ideas that quantum maximum-likelihood decoding must account for stabilizer degeneracy, that logical-class likelihoods can be expressed as partition functions, and that exact or approximate tensor/factor-graph contraction can be used for quantum decoding are established prior art.

Likewise, compiling probabilistic inference into reusable arithmetic/decision circuits, and evaluating compiled objects over different evidence assignments or semirings, is established in the probabilistic-inference and knowledge-compilation literature.

The publication opportunity is therefore not “tensor-network decoding”, “degenerate decoding”, “variable elimination”, or “compile once, query many” in the abstract.

The strongest currently defensible QTR contribution is narrower: the code-specific construction and verification of an exact **selector-parametric compiled query object** for degenerate qLDPC decoding. The 2026 coset-MRF paper uses essentially the same affine coset parameterization at the fixed-class level, so the affine selector/stabilizer factorization itself is no longer treated as a novelty candidate.

The remaining candidate contribution is:

- one unified syndrome-plus-logical selector interface;
- exact symbolic elimination that retains those selector variables rather than fixing a class before elimination;
- canonical reusable compiled objects;
- preservation of full score, canonical-class, minimum-representative, tie-set, and deterministic-decision semantics;
- cross-checking across several exact algebras;
- a controlled progression from exhaustive C18 semantics to C72 and the active C90 frontier.

Whether the selector-parametric object is genuinely absent from the closest 2026 work remains an explicit audit question, not an assumed distinction.

A second, potentially stronger publication result is conditional on completion of `QTR-C90-EXACT-DECODER-001`: exact degeneracy-aware logical-class inference on the protected `[[90,8,10]]` bivariate-bicycle instance and frozen C90 corpus. Targeted literature search performed for this audit did not identify a published exact degenerate maximum-likelihood result for this C90 instance. That negative search result is not a priority certificate and must be repeated before submission.

## 3. Closest prior art

### 3.1 Degenerate maximum-likelihood and tensor-network decoding

Ferris and Poulin established a formal relationship between quantum decoding and tensor-network contraction:

- Andrew J. Ferris and David Poulin, “Tensor Networks and Quantum Error Correction”, *Physical Review Letters* 113, 030501 (2014), DOI 10.1103/PhysRevLett.113.030501.

Bravyi, Suchara and Vargo gave exact and approximate maximum-likelihood decoding methods for the surface code:

- Sergey Bravyi, Martin Suchara and Alexander Vargo, “Efficient Algorithms for Maximum Likelihood Decoding in the Surface Code”, *Physical Review A* 90, 032326 (2014), arXiv:1405.4883.

Chubb developed a general tensor-network decoder for two-dimensional Pauli codes:

- Christopher T. Chubb, “General tensor network decoding of 2D Pauli codes”, arXiv:2101.04125.

Piveteau, Chubb and Renes extended tensor-network decoding beyond 2D, including noisy-syndrome settings:

- Christophe Piveteau, Christopher T. Chubb and Joseph M. Renes, “Tensor-Network Decoding Beyond 2D”, *PRX Quantum* 5, 040303 (2024), DOI 10.1103/PRXQuantum.5.040303.

These works preclude any broad claim that QTR invented tensor-network decoding, contraction-based decoding, or degeneracy-aware likelihood summation.

### 3.2 qLDPC and BP+OSD baselines

BP with ordered-statistics post-processing is established qLDPC practice:

- Joschka Roffe, David R. White, Simon Burton and Earl Campbell, “Decoding across the quantum low-density parity-check code landscape”, *Physical Review Research* 2, 043423 (2020).
- Pavel Panteleev and Gleb Kalachev, “Degenerate Quantum LDPC Codes With Good Finite Length Performance”, *Quantum* 5, 585 (2021), arXiv:1904.02703.

The bivariate-bicycle code family and the `[[72,12,6]]`, `[[90,8,10]]`, `[[108,8,10]]`, `[[144,12,12]]`, `[[288,12,18]]` and `[[784,24,24]]` instances originate in:

- Sergey Bravyi, Andrew W. Cross, Jay M. Gambetta, Dmitri Maslov, Patrick Rall and Theodore J. Yoder, “High-threshold and low-overhead fault-tolerant quantum memory”, *Nature* 627, 778–782 (2024), arXiv:2308.07915.

QTR does not have priority over these codes or conventional decoding baselines.

### 3.3 2026 exact/certified qLDPC decoding result

The closest current scientific competitor is:

- Ragavi Krishnamoorthy et al., “Certified decoding of quantum LDPC codes”, arXiv:2608.25545 (submitted 2026-08-26).

That work:

- formulates logical-class probabilities as partition functions of a positive Markov random field over check variables;
- develops certified approximate inference;
- uses elimination clusters / bucket elimination;
- reports exact degenerate maximum-likelihood decoding of the `[[72,12,6]]` bivariate-bicycle code;
- reports an induced width of approximately 23 for its C72 coset graph;
- extends the framework to noisy-syndrome and circuit-level problems.

Accordingly, the following claims are not available to QTR:

- “first exact degenerate decoder for a qLDPC code”;
- “first exact degenerate decoder for the `[[72,12,6]]` BB code”;
- “first graphical-model formulation of degenerate qLDPC decoding”;
- “first use of elimination clusters for exact qLDPC decoding”.

The mathematical overlap is closer than a generic “different graphical model” comparison suggests. Krishnamoorthy et al. write each class as (e_lambdaoplus u^T H_X) and factor its probability into one local potential per qubit over incident X-check variables. QTR writes the same underlying coset object as (L aoplus S z), using an independent stabilizer basis and a unified syndrome/logical selector coordinate. The affine coset factorization and local qubit-factor construction must therefore be treated as overlapping prior art.

The QTR C72 representation has 30 independent stabilizer variables where the published coset MRF reports 36 check variables. Its recorded min-fill width 18 must not be presented as directly smaller than the approximately-23 width reported by Krishnamoorthy et al. without a common graph definition, common preprocessing, and controlled comparison.

### 3.4 Probabilistic knowledge compilation

Compile-once exact inference is established outside QEC.

Relevant foundations include:

- Mark Chavira and Adnan Darwiche, “Compiling Bayesian Networks Using Variable Elimination”, IJCAI 2007. The work compiles variable-elimination traces into arithmetic circuits and explicitly targets multiple subsequent queries.
- Adnan Darwiche, “A Differential Approach to Inference in Bayesian Networks”, *Journal of the ACM* 50(3), 2003.
- Angelika Kimmig, Guy Van den Broeck and Luc De Raedt, “Algebraic model counting”, *Journal of Applied Logic* 22, 46–62 (2017), DOI 10.1016/j.jal.2016.11.031.
- Giso H. Dal et al., “A compositional approach to probabilistic knowledge compilation”, *International Journal of Approximate Reasoning* 138, 38–66 (2021).
- Cory Butz et al., “Arithmetic Circuit Compilation Using Symbolic Probabilistic Inference and Indicator-Determined Buckets” (2024).

This literature establishes reusable compiled inference, symbolic parameters/evidence, structured DAG/circuit representations, and semiring-general evaluation.

Therefore QTR must not claim novelty for arithmetic circuits, hash-consed DAGs, symbolic variable elimination, semirings, or amortized compilation in isolation.

## 4. Claim-by-claim novelty disposition

| Candidate claim | Disposition | Reason |
|---|---|---|
| Degenerate decoding should sum over stabilizer-equivalent errors | prior art | Core ML-decoding principle is established. |
| Quantum decoding can be represented by tensor/factor networks | prior art | Ferris–Poulin and later work. |
| Exact variable elimination can decode quantum codes | prior art | Surface-code and qLDPC exact results exist. |
| Exact C72 degenerate ML decoding | preempted | Krishnamoorthy et al. 2026 explicitly report it. |
| Compile probabilistic inference once, answer many queries later | prior art | Arithmetic-circuit / knowledge-compilation literature. |
| Evaluate compiled inference under semiring variants | prior art in general | Algebraic model counting and semiring inference. |
| Exact affine selector/stabilizer reparameterization for BB decoding | **substantially overlapping prior art** | The 2026 coset-MRF construction uses the same fixed-class affine stabilizer-coset parameterization in different coordinates. |
| Canonical selector-parametric QEC compilation preserving full score/tie/correction semantics | **plausible publication contribution, audit still open** | General compilation and the underlying coset factorization are prior art; targeted review has not yet identified a QEC construction that retains the unified syndrome/logical selector symbolically through elimination in one reusable exact object. |
| Exact equivalence chain: exhaustive representatives → transfer → degeneracy VE → compiled selector DAG | **plausible publication contribution** | Strong reference/oracle contribution even if primitives are known. |
| Exact finite BB structural ladder under one frozen protocol | useful dataset/methodological contribution | Methods are standard; exact controlled cross-instance record may be publishable as supporting evidence. |
| C90 resource-bound decomposition into peak/work/retained/physical gates | useful methodological contribution | Strong negative/diagnostic result; unlikely headline novelty alone. |
| Exact degenerate logical-class inference on `[[90,8,10]]` BB | **high-priority novelty candidate, conditional** | Targeted search found many approximate/practical C90 decoders but no published exact degenerate-ML C90 result. Requires completed external run and renewed exhaustive search. |
| General TCM superiority over BP/BP-OSD | unsupported | Existing QTR evidence is finite and non-dominating; claim prohibited. |
| qLDPC scaling law / bounded family treewidth | unsupported | QTR ladder is finite and named-order only. |

## 5. Utility independent of novelty

Even if a mechanism is not historically first, the workset has substantial utility.

### 5.1 Exact oracle and benchmark utility

QTR preserves exact logical-class scores, winning-class ties, correction representatives and correctness outcomes rather than only logical-error-rate totals. This can support:

- regression testing of approximate qLDPC decoders;
- diagnosis of BP/BP-OSD, beam-search, neural and sampling-decoder errors;
- calibration of uncertainty/certification methods;
- benchmarking tie handling and degeneracy sensitivity;
- controlled study of objective mismatch between minimum-weight and maximum-class-probability decisions.

### 5.2 Representation-design utility

The exact C18 representation chain isolates what each representation changes and what it preserves. This is useful for studying:

- where width is introduced;
- when local width reduction increases repeated work;
- when symbolic sharing amortizes repeated selector queries;
- which structural changes preserve exact semantics;
- how conservative static resource bounds differ from actual retained structures.

### 5.3 Negative-result utility

The temporal decomposition and C90 bound programmes provide structured negative evidence rather than timeouts:

- three exact temporal auxiliary-state rewrites did not improve the frozen deterministic width;
- the original C90 peak-table cap was shown not to be the sole blocker;
- later studies separated cumulative work, retained representation size and physical-host feasibility;
- upper-bound failure was explicitly not converted into an infeasibility theorem.

This is useful methodological evidence for exact-inference design.

### 5.4 Reproducibility utility

The programme's strongest engineering contribution is unusually strict provenance:

- frozen corpora;
- exact source and artifact identities;
- independent correctness oracles;
- pre-outcome manifests;
- immutable scientific snapshots;
- explicit missing-cell semantics;
- quality-blind validation before scoring;
- separation of compute from governance.

These properties make the resulting datasets and exact decoders potentially useful as community reference artifacts.

## 6. Recommended publication decomposition

### Paper A — method paper

Working title:

**Compiled Exact Degenerate Inference for Bivariate-Bicycle Quantum LDPC Codes**

Core contribution:

A code-specific exact inference compiler that retains syndrome/logical selector coordinates symbolically while eliminating stabilizer degeneracy, producing reusable canonical compiled objects whose evaluations preserve exact score, tie, canonical-class and correction semantics.

Required positioning:

- cite knowledge compilation as conceptual prior art;
- cite tensor-network and graphical-model decoding as QEC prior art;
- explicitly contrast with Krishnamoorthy et al. rather than claiming first exact C72 decoding;
- demonstrate what is distinct about the selector-parametric construction and semantic object preserved.

Primary evidence:

- C18 complete equivalence chain;
- C72 exact compilation and frozen oracle validation;
- C90 only as a conditional stress case unless the external campaign closes before submission.

### Paper B — C90 result paper

Working title:

**Exact Degenerate Logical-Class Inference on the `[[90,8,10]]` Bivariate-Bicycle Code**

Status:

**Conditional. Do not draft results or novelty claims before authoritative external execution closes.**

Core contribution if successful:

- exact C90 compiled inference for the frozen BSC one-sector problem;
- exact 256-class decisions on each of 347 frozen inputs;
- corrections fixed before quality exposure;
- independent matched comparison with the protected historical conventional rows;
- complete artifact and receipt release.

This paper must not present the 347-input corpus as an exhaustive syndrome-domain performance study.

## 7. Publication theorem obligations

A credible method paper should replace implementation-only confidence with explicit mathematical statements.

At minimum:

1. **Affine selector decomposition theorem.** Show that the chosen independent syndrome and logical functionals define the selector coordinate used by the exact class representation.
2. **Degeneracy-factorization theorem.** Show that summing/minimizing over the stabilizer variables computes the declared class objective.
3. **Compilation correctness theorem.** For every selector assignment, evaluation of the compiled symbolic DAG equals fixed-selector variable elimination under the same algebra.
4. **Canonical correction theorem.** Show that the min-plus/product payload recovers both the minimum-weight representative and canonical class key under the declared tie order.
5. **Decision preservation corollary.** Exact score-table equality implies equality of winning-class tie sets and deterministic correction decisions.
6. **No-hidden-quality lemma for the evaluation protocol.** The selector-evaluation stage is independent of injected-error correctness labels and conventional outcomes.

These claims should be stated independently of Python/C++ implementation details and then connected to executable verification.

## 8. Missing evidence before submission

### For Paper A

- theorem-quality proof of compilation correctness for arbitrary selector assignments;
- explicit comparison of the QTR factorization to the 2026 coset-MRF construction;
- common-definition structural comparison on C72 rather than comparing incompatible width numbers;
- wall-clock measurements only if carefully separated from the scientific exactness claim;
- released machine-readable exact C18 oracle object and C72 validation object;
- refreshed literature audit immediately before submission.

### For Paper B

- all 768 external work units complete under the protected external execution profile;
- all 266,496 authoritative selector evaluations generated externally;
- all 347 corrections fixed before scoring;
- independent matched comparison completed;
- no use of retired GitHub-hosted selector values in the authoritative result;
- exact receipt inventory and public reproduction instructions;
- renewed search for any exact C90 degenerate-decoding result published after this audit date.

## 9. Red-line claims

The following wording is prohibited unless new evidence specifically supports it:

- “first exact qLDPC decoder”;
- “first exact C72 decoder”;
- “first tensor-network qLDPC decoder”;
- “first compile-once probabilistic inference”;
- “first semiring inference compiler”;
- “TCM beats BP”;
- “TCM scales to qLDPC families”;
- “C90 exact decoding is practical”;
- “the C90 representation is intrinsically hard”;
- “the finite ladder establishes asymptotic scaling”;
- “the temporal representation family is exhaustive in general”.

## 10. Current publication disposition

**Proceed with Paper A immediately as a method/equivalence manuscript.**

**Prepare Paper B as a conditional shell only.**

The decisive near-term technical task for publication is not another broad benchmark. It is to formalize and prove the selector-parametric compilation theorem and to build a controlled side-by-side comparison with the 2026 coset-MRF/elimination-cluster formulation.

The decisive scientific task for Paper B remains completion of the fully external C90 exact campaign.
