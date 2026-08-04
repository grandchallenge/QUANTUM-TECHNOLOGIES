# GCL-GHOS-QUANTUM-POST-REPAIR-READBACK-001

## Evidence identity

- repository: `grandchallenge/QUANTUM-TECHNOLOGIES`;
- protected baseline: `a8f2441cd75e717ff30f05d32c0f5e90a7dd7394`;
- readback issue: `grandchallenge/QUANTUM-TECHNOLOGIES#25`;
- recorded at: `2026-08-04T07:20:26.7913380Z`;
- authenticated actor: `fyremael` (`17925951`), repository admin;
- canonical receipt SHA-256: `83109c5c7f7461480bc5f0119c96295716a194a71dce3fdebe3552d8602efe37`;
- admitted source-bundle SHA-256: `3d17fbc44356c614a0b96c9f0aa3973fc4653f7fa85ebd8bc576cf4f7cf48080`;
- source projections: `16`;
- readback gaps: `0`.

## Verified state

The admitted readback binds the live repository merge settings, protected-main
ruleset `20106953`, immutable release-tag ruleset `20355165`, vulnerability
alerts and dependency graph, active Dependabot security updates, private
vulnerability reporting, CodeQL default setup, protected workflow identities,
governed surface identities, and the previously admitted execution receipt on
protected `main`.

The source bundle preserves every retained raw projection byte-for-byte in
base64 form and binds each entry by byte count and SHA-256.

## Validation

The repository-discovered unittest validates the closed schema, exact receipt
digest, admitted source-bundle identity and exact projection reconstruction,
source ledger concordance, settings and ruleset semantics, security controls,
workflow and governed-surface identities, admitted execution evidence, zero
readback gaps, credential absence, and claim boundaries. Adversarial mutations
reject omission, authority drift, settings drift, ruleset drift, security drift,
workflow/surface drift, source corruption, unsupported inference, credential
material, and claim promotion.

## Boundary

This attestation admits a post-repair governance readback only. It does not
itself dispose `QUANTUM-P1-001` or `QUANTUM-P2-001`, close issues #21 or #14,
establish repository or organization-wide conformance, certify mathematics,
prove quantum advantage, validate hardware, or authorize deployment,
manufacturing, product, or commercial claims. Those dispositions remain for
the replacement `gcl-standards` deviation-ledger overlay.
