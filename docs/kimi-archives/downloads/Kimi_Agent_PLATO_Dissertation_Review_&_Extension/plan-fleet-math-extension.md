# Fleet Mathematics Extension — Execution Plan

## Context
The user asks to review and extend Fleet Mathematics sections of the PLATO dissertation. Key constraint: Laman→Zhao, H1→β₁, BFT table, and Pythagorean48 collision analysis are ALREADY FIXED — do not re-do.

## Extension Tasks (Pick 2-3)
Selected:
1. **Non-tautological emergence definition** — Define emergence as d(β₁)/dt crossing zero, not β₁ > 0. Reference Scheffer et al. critical slowing down + persistence stability theorem.
2. **Formal Zero Holonomy Consensus proof** — Formal complexity bound: O(N) cycle discovery + O(1) per-cycle holonomy check. Compare vs PBFT 3-phase commit.
3. **Rigidity-Holonomy Bridge proof formalization** — Prove: G generically bearing-rigid in ℝ³ → cycle holonomy is well-defined (independent of embedding). Core theorem linking 12-neighbor bound to zero holonomy.

## Stage 1: Material Ingestion (Parallel)
- Read CHAPTER-09, CHAPTER-10, CHAPTER-14, APPENDIX-B from GitHub
- Read holonomy-consensus code (consensus.rs, cohomology.rs, encoding.rs)
- Read flux-core/src/lib.rs for FLUX-C formalization
- Read constraint-theory-llvm/src/lib.rs for LLVM backend

## Stage 2: Extension Writing (Parallel)
- Agent 1: Non-tautological emergence definition → APPENDIX-C
- Agent 2: Formal ZHC proof + complexity bounds → APPENDIX-D
- Agent 3: Rigidity-Holonomy Bridge theorem → APPENDIX-E

## Stage 3: Integration
- Line-level corrections to existing chapters where needed
- New appendices with LaTeX math
- Push to fleet-math-extension branch
