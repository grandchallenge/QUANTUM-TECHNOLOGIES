# QTR Paper A — Verified Bibliography and Source-Scope Audit

Status: \`BIBLIOGRAPHY_METADATA_CHECKED__SUBMISSION_INTEGRITY_REVIEW_OPEN\`

Date: 2026-11-19

Subject: \`publication/manuscripts/COMPILED-EXACT-DEGENERATE-INFERENCE-DRAFT.md\`; 12 numbered citations.

## Verification rule

Each item below was checked against the linked journal/publisher, IJCAI proceedings, institutional publication record, or arXiv record. This is a factual bibliographic audit, not a copyright license review or a comprehensive priority search. Cite the actual source for reported science; verification of metadata is not verification of every claim in that paper.

| No. | Reference metadata | Verified source |
|---|---|---|
| 1 | Andrew J. Ferris and David Poulin (2014), *Physical Review Letters* **113**, 030501 | [APS / DOI 10.1103/PhysRevLett.113.030501](https://doi.org/10.1103/PhysRevLett.113.030501) |
| 2 | Sergey Bravyi, Martin Suchara and Alexander Vargo (2014), *Physical Review A* **90**, 032326 | [APS / DOI 10.1103/PhysRevA.90.032326](https://doi.org/10.1103/PhysRevA.90.032326) |
| 3 | Christopher T. Chubb, *General tensor network decoding of 2D Pauli codes*, arXiv:2101.04125 (first posted 2021) | [arXiv record](https://arxiv.org/abs/2101.04125), [ETH research collection](https://www.research-collection.ethz.ch/entities/publication/d253ceb0-2a36-4c0b-aef8-032de45f5489) |
| 4 | Christophe Piveteau, Christopher T. Chubb and Joseph M. Renes (2024), *PRX Quantum* **5**, 040303 | [APS / DOI 10.1103/PRXQuantum.5.040303](https://doi.org/10.1103/PRXQuantum.5.040303) |
| 5 | Joschka Roffe, David R. White, Simon Burton and Earl Campbell (2020), *Physical Review Research* **2**, 043423 | [APS / DOI 10.1103/PhysRevResearch.2.043423](https://doi.org/10.1103/PhysRevResearch.2.043423) |
| 6 | Pavel Panteleev and Gleb Kalachev (2021), *Quantum* **5**, 585 | [Quantum / DOI 10.22331/q-2021-11-22-585](https://doi.org/10.22331/q-2021-11-22-585) |
| 7 | Sergey Bravyi, Andrew W. Cross, Jay M. Gambetta, Dmitri Maslov, Patrick Rall and Theodore J. Yoder (2024), *Nature* **627**, 778–782 | [Nature / DOI 10.1038/s41586-024-07107-7](https://doi.org/10.1038/s41586-024-07107-7) |
| 8 | Ragavi Krishnamoorthy and ten coauthors, *Certified decoding of quantum LDPC codes*, arXiv:2608.25545v1 (submitted 2026-08-26) | [arXiv HTML v1](https://arxiv.org/html/2608.25545v1), [arXiv record](https://arxiv.org/abs/2608.25545) |
| 9 | Adnan Darwiche (2003), *Journal of the ACM* **50**(3), 280–305 | [DOI 10.1145/765568.765570](https://doi.org/10.1145/765568.765570) |
| 10 | Mark Chavira and Adnan Darwiche (2007), *Proceedings of IJCAI-07*, 2443–2448 | [IJCAI proceedings](https://ijcai.org/proceedings/2007/393) |
| 11 | Angelika Kimmig, Guy Van den Broeck and Luc De Raedt (2017), *Journal of Applied Logic* **22**, 46–62 | [DOI 10.1016/j.jal.2016.11.031](https://doi.org/10.1016/j.jal.2016.11.031) |
| 12 | Michele Banfi, Marco Ferrari, Antonino Favano, Alberto Tarable and Luca Barletta, *Certified Non-Degenerate Maximum-Likelihood Benchmarking of Quantum LDPC Decoders*, arXiv:2610.28008v1 (submitted 2026-10-20) | [arXiv record](https://arxiv.org/abs/2610.28008) |

## Scientific comparison safeguards

The closest exact qLDPC manuscript, Krishnamoorthy et al. arXiv:2608.25545v1, Section 8.5, tests 120 code-capacity C72 syndromes at each of \(p=0.03\) and \(p=0.05\), yielding 240 exact-reference comparisons. A full 4,096-logical-class global optimum is additionally checked on a **subsample** using mini-bucket screening with exact surviving-class evaluation. That is not the same test as GCL's 300 frozen selector-level compiler/oracle checks or its separate 329-input three-algebra C72 interface campaign. The manuscript may discuss complementary mathematical mechanisms; it must not treat the three corpora as matched trials.

Banfi et al. arXiv:2610.28008 benchmark **non-degenerate** maximum-likelihood decisions under circuit-level noise. Paper A's BSC sum-product objective is **degenerate** class-likelihood aggregation. The two objectives are not interchangeable. Distinguish min-plus representative selection from sum-product class partition when describing related work.

Chavira and Darwiche (IJCAI-07) already compile variable elimination using algebraic decision diagrams and support multiple evidence queries. General reusable compiled inference, hash-consing, marginalization distributivity and semiring evaluation are **prior art**; QTR's publication proposal should stay confined to its QEC-specific selector/stabilizer interface and finite certified semantics.

## Remaining pre-submission obligations

- Recheck the latest versions of all 2026 preprints immediately before public submission and preserve versions cited in the public manuscript; current text's specific comparisons are anchored to v1.
- Perform the already specified *source-level* comparison against the other group's implementation if made available; absent code is an explicit evidence limit, not a priority argument.
- Independently review the corrected full-kernel and restricted-domain semiring theorem, including reference-code implementation correspondence.
- Finish figures, output package and metadata; explicitly assign the human author list, affiliations, acknowledgments and corresponding author before submission.
- Verify final manuscript citation alignment and accessibility of each released evidence artifact.

No scientific evidence, mathematical claim status or publication authority is altered by this audit.
