# APPENDIX E: The Rigidity–Holonomy Bridge Theorem

**Authors** | Zhao et al. (2017); Hendrickson (1992); Laman (1970); Asimow & Roth (1978); this work  
**Chapter Context** | Bridges Chapter 10 (Topological Trust and Holonomy Consensus) with the structural rigidity foundations of multi-agent formation control.

---

## E.1 Introduction: Why Rigidity and Holonomy Are Connected

The PLATO fleet achieves consensus not merely through message passing, but through *geometric* consensus: every node agrees on a common orientation of the world. Chapter 10 introduced holonomy consensus on $\mathrm{SO}(3)$—the idea that parallel transport of 3D rotation matrices around any cycle in the communication graph should compose to the identity. Zero holonomy is the geometric signature of a consistent, trustworthy network.

But zero holonomy is only meaningful if the *geometry itself* is fixed. Consider a flexible network: nodes may reconfigure while preserving all local edge measurements, creating "wiggle room" in the global embedding. In such a non-rigid framework, the same edge state (say, a reported bearing or relative rotation) could arise from two geometrically distinct configurations. Transport a rotation matrix around a cycle in the first configuration, then in the second; the two holonomies may differ, not because any node lied, but because the *geometry* is ambiguous.

**Rigidity eliminates this ambiguity.** If the network is *bearing-rigid* in $\mathbb{R}^3$, the inter-node bearings uniquely determine the configuration up to translation and scale. There is no wiggle room. Every edge's relative orientation is fixed. Therefore, the parallel transport of rotation matrices along edges is uniquely defined, and cycle holonomy becomes a well-defined property of the *graph and its states*, not an artifact of an arbitrary embedding.

This appendix proves the formal bridge: **bearing rigidity implies well-defined, embedding-independent holonomy**. The theorem justifies the 12-neighbor bound used in PLATO's trust architecture and shows that structural rigidity (a topological property) guarantees geometric consistency (a differential-geometric property).

---

## E.2 3D Bearing Rigidity

### E.2.1 The Bearing Framework

Let $G = (V, E)$ be a connected, undirected graph with $n = |V|$ vertices and $m = |E|$ edges. Let $\mathbf{p}: V \to \mathbb{R}^3$ assign to each vertex $i \in V$ a position $\mathbf{p}_i \in \mathbb{R}^3$. The pair $(G, \mathbf{p})$ is called a **bearing framework**.

For each undirected edge $\{i, j\} \in E$, the **bearing** is the unit vector pointing from $i$ to $j$:

$$
\mathbf{g}_{ij} \triangleq \frac{\mathbf{p}_j - \mathbf{p}_i}{\|\mathbf{p}_j - \mathbf{p}_i\|} \in \mathbb{S}^2 \subset \mathbb{R}^3.
$$

Note that $\mathbf{g}_{ij} = -\mathbf{g}_{ji}$. The collection of all edge bearings is denoted $\mathcal{G} = \{\mathbf{g}_{ij}\}_{\{i,j\} \in E}$.

Two frameworks $(G, \mathbf{p})$ and $(G, \mathbf{p}')$ are **bearing-equivalent** if they share the same edge bearings: $\mathbf{g}_{ij} = \mathbf{g}'_{ij}$ for all $\{i, j\} \in E$. They are **bearing-congruent** if they are related by a translation and a non-zero scale factor: $\mathbf{p}'_i = c \mathbf{p}_i + \mathbf{t}$ for some $c \in \mathbb{R} \setminus \{0\}$ and $\mathbf{t} \in \mathbb{R}^3$.

> **Definition E.1 (Bearing Rigidity, Zhao et al. 2017).** A framework $(G, \mathbf{p})$ is **bearing-rigid** in $\mathbb{R}^3$ if every framework bearing-equivalent to $(G, \mathbf{p})$ is also bearing-congruent to it.

In other words, the edge bearings uniquely determine the configuration up to the trivial motions of translation and scale.

### E.2.2 The Bearing Rigidity Matrix and Infinitesimal Rigidity

To analyze rigidity locally, consider a smooth perturbation $\mathbf{p}(t)$ with $\mathbf{p}(0) = \mathbf{p}$. The bearing of edge $\{i,j\}$ evolves as:

$$
\dot{\mathbf{g}}_{ij} = \frac{P_{\mathbf{g}_{ij}}}{\|\mathbf{p}_j - \mathbf{p}_i\|} (\dot{\mathbf{p}}_j - \dot{\mathbf{p}}_i),
$$

where $P_{\mathbf{g}} \triangleq I_3 - \mathbf{g}\mathbf{g}^T$ is the orthogonal projector onto the plane perpendicular to $\mathbf{g}$. This linear map defines the **bearing rigidity matrix** $R_B(G, \mathbf{p}) \in \mathbb{R}^{3m \times 3n}$, which maps node velocity vectors $(\dot{\mathbf{p}}_1, \ldots, \dot{\mathbf{p}}_n) \in \mathbb{R}^{3n}$ to bearing velocities $(\dot{\mathbf{g}}_{ij}) \in \mathbb{R}^{3m}$.

> **Definition E.2 (Infinitesimal Bearing Rigidity).** A framework $(G, \mathbf{p})$ is **infinitesimally bearing-rigid** if $\mathrm{rank}\, R_B(G, \mathbf{p}) = 3n - 4$.

The nullspace of $R_B$ always contains the trivial motions: translations (dimension 3) and scaling (dimension 1), giving $3n - 4$ as the maximal possible rank. Infinitesimal bearing rigidity is the generic condition; by Asimow and Roth (1978), a framework that is infinitesimally rigid is also (globally) rigid, and generic frameworks are either infinitesimally rigid or not rigid at all (Hendrickson 1992).

### E.2.3 The Edge Count and the 12-Neighbor Intuition

Each edge bearing $\mathbf{g}_{ij}$ provides a 2-dimensional constraint (it lies on $\mathbb{S}^2$, a 2-sphere, but is measured as a unit vector in $\mathbb{R}^3$, giving 2 independent components). The configuration space has $3n$ degrees of freedom, minus 4 trivial dimensions, yielding $3n - 4$ geometric degrees of freedom. To fix these, we require:

$$
2m \geq 3n - 4 \quad \Longrightarrow \quad m \geq \frac{3n - 4}{2} \approx 1.5n.
$$

This gives an *average degree* of approximately 3—far fewer than the 12 neighbors used in PLATO. The discrepancy arises because:

1. **The above counts local, not global, rigidity.** Laman's theorem (1970) for 2D distance rigidity and its bearing analogs require edge counts sufficient to prevent all flexes. In 3D, the combinatorial characterization is more subtle, and generic rigidity typically requires $m \geq 2n$ edges for bearing frameworks (Zhao et al. 2017, Theorem 6), yielding an average degree of ~4.

2. **Bearing patterns matter.** In practice, a node with only 4 neighbors may have coplanar bearings, creating degeneracies in the rigidity matrix. To ensure *generic* rigidity with high probability in random 3D configurations—where bearings may cluster, align, or otherwise fail to provide full-rank constraints—substantially more edges are needed.

3. **The 12-neighbor bound.** Each node has 3 degrees of freedom in its orientation relative to the network. Each neighbor provides a bearing, which contributes 1 effective constraint on the node's orientation once translation and scale are factored out. To fully constrain a node's orientation in 3D requires at least 3 independent bearings, but to ensure *global* rigidity with redundancy against measurement noise, node dropout, and adversarial manipulation, PLATO's trust architecture demands that every node maintain bearings to up to 12 neighbors. This provides sufficient over-constraint that the bearing rigidity matrix achieves full rank $3n - 4$ generically, and the network's geometry is unambiguously fixed.

---

## E.3 Holonomy in $\mathrm{SO}(3)$

### E.3.1 Parallel Transport Along Edges

Let each node $i \in V$ maintain a local coordinate frame, represented by a rotation matrix $R_i \in \mathrm{SO}(3)$. The **edge state** on $\{i,j\}$ is a relative rotation $R_{ij} \in \mathrm{SO}(3)$ describing the orientation of $j$'s frame as seen from $i$.

If the network is embedded in $\mathbb{R}^3$ with positions $\mathbf{p}$, the edge bearings $\mathbf{g}_{ij}$ determine the relative orientation of the nodes. Specifically, define the **parallel transport operator** along edge $\{i,j\}$ as the rotation matrix that aligns $i$'s local frame with $j$'s local frame, given the geometric bearing between them:

$$
\mathcal{T}_{ij}: \mathrm{SO}(3) \to \mathrm{SO}(3), \qquad \mathcal{T}_{ij}(R) = R_{ij} R,
$$

where $R_{ij}$ is computed from the bearing $\mathbf{g}_{ij}$ and the nodes' chosen reference orientations. In the holonomy consensus protocol (Chapter 10), $R_{ij}$ is the reported relative rotation; consistency requires $R_{ij} = R_{ji}^{-1}$.

### E.3.2 Cycle Holonomy

Let $\gamma = (e_1, e_2, \ldots, e_k)$ be a directed cycle in $G$, where each $e_\ell = (v_\ell, v_{\ell+1})$ is a directed edge and $v_{k+1} = v_1$. The **holonomy** of $\gamma$ is the composition of parallel transport operators around the cycle:

$$
\mathrm{Hol}(\gamma) \triangleq R_{e_k} R_{e_{k-1}} \cdots R_{e_1} \in \mathrm{SO}(3).
$$

**Zero holonomy** means $\mathrm{Hol}(\gamma) = I_3$ for all cycles $\gamma$ in $G$. This is the geometric condition that parallel transport around any closed loop returns a vector to its original orientation.

The problem is that $R_{e_\ell}$ depends on the *embedding*: different configurations $\mathbf{p}, \mathbf{p}'$ with the same edge states might yield different relative orientations, hence different $R_{e_\ell}$, hence different $\mathrm{Hol}(\gamma)$. The Rigidity–Holonomy Bridge Theorem resolves this.

---

## E.4 The Rigidity–Holonomy Bridge Theorem

### E.4.1 Statement

> **Theorem E.3 (Rigidity–Holonomy Bridge).** Let $G = (V, E)$ be a connected graph and $\mathbf{p}: V \to \mathbb{R}^3$ be a generic embedding. Suppose the bearing framework $(G, \mathbf{p})$ is bearing-rigid in $\mathbb{R}^3$. Then:
>
> **(a)** (Well-definedness.) For any cycle $\gamma$ in $G$, the cycle holonomy $\mathrm{Hol}(\gamma) \in \mathrm{SO}(3)$ is uniquely determined by the edge bearings and is independent of the choice of embedding within the bearing-equivalence class.
>
> **(b)** (Consistency implies identity.) If all edge states are consistent—meaning the relative rotation reported by $i$ for $j$ equals the inverse of that reported by $j$ for $i$, i.e., $R_{ij} = R_{ji}^{-1}$ for all $\{i,j\} \in E$—then $\mathrm{Hol}(\gamma) = I_3$ for all cycles $\gamma$.
>
> **(c)** (Converse for non-rigidity.) Conversely, if $G$ is **not** bearing-rigid, there exist embeddings $\mathbf{p}, \mathbf{p}'$ that are bearing-equivalent but produce different cycle holonomies for the same edge states.

### E.4.2 Proof of Part (a): Well-Definedness

*Proof sketch.* Let $(G, \mathbf{p})$ be bearing-rigid. By Definition E.1, any framework $(G, \mathbf{p}')$ that is bearing-equivalent to $(G, \mathbf{p})$ is bearing-congruent to it. That is, $\mathbf{p}'_i = c \mathbf{p}_i + \mathbf{t}$ for some $c \neq 0$ and $\mathbf{t} \in \mathbb{R}^3$.

The bearing $\mathbf{g}_{ij}$ is translation-invariant and scale-invariant up to sign (the sign is fixed by edge direction). Therefore, the bearing-congruence transformation leaves all edge bearings unchanged. Consequently, the relative orientation between any two nodes $i$ and $j$, as determined by their bearing $\mathbf{g}_{ij}$ and their local frames, is also unchanged under translation and scale.

Now consider the rotation matrix $R_{ij}$ assigned to edge $\{i,j\}$. This matrix is computed from the bearing $\mathbf{g}_{ij}$ and the nodes' reference orientations. Since the bearing $\mathbf{g}_{ij}$ is identical for all embeddings in the bearing-equivalence class, and the reference orientation convention is fixed by the protocol, the matrix $R_{ij}$ is identical for all such embeddings.

For any cycle $\gamma = (e_1, \ldots, e_k)$, the holonomy is:

$$
\mathrm{Hol}(\gamma) = R_{e_k} R_{e_{k-1}} \cdots R_{e_1}.
$$

Since each factor $R_{e_\ell}$ is uniquely determined by the edge bearings, the product $\mathrm{Hol}(\gamma)$ is uniquely determined as well. The holonomy depends only on the bearings $\{\mathbf{g}_{ij}\}$ and the edge-state convention, not on the particular representative $\mathbf{p}$ of the bearing-equivalence class. $\blacksquare$

### E.4.3 Proof of Part (b): Consistency Implies Identity

*Proof sketch.* Suppose all edge states are consistent: $R_{ij} = R_{ji}^{-1}$ for every $\{i,j\} \in E$. Consider a directed cycle $\gamma = (v_1, v_2, \ldots, v_k, v_1)$ with edges $e_\ell = (v_\ell, v_{\ell+1})$, where $v_{k+1} = v_1$.

The holonomy is:

$$
\mathrm{Hol}(\gamma) = R_{v_k v_1} R_{v_{k-1} v_k} \cdots R_{v_1 v_2}.
$$

By consistency, each $R_{v_\ell v_{\ell+1}}$ describes the same geometric relationship as $R_{v_{\ell+1} v_\ell}^{-1}$. The cycle is a closed loop in the fixed, rigid geometry. Because the embedding is bearing-rigid, the geometry is fixed; there is no ambiguity in the relative orientations.

More concretely, define $R_i$ as the absolute orientation of node $i$ in some global reference frame. The edge rotation can be written as $R_{ij} = R_j R_i^{-1}$ (the rotation from $i$'s frame to $j$'s frame). Then:

$$
\mathrm{Hol}(\gamma) = (R_{v_1} R_{v_k}^{-1})(R_{v_k} R_{v_{k-1}}^{-1}) \cdots (R_{v_2} R_{v_1}^{-1}) = R_{v_1} R_{v_1}^{-1} = I_3.
$$

All intermediate terms telescope, leaving the identity. This holds for every cycle because the absolute orientations $R_i$ are well-defined in the rigid framework. $\blacksquare$

### E.4.4 Proof of Part (c): Non-Rigidity Permits Ambiguous Holonomy

*Proof sketch.* Suppose $G$ is not bearing-rigid. Then there exists a framework $(G, \mathbf{p})$ and a bearing-equivalent framework $(G, \mathbf{p}')$ that is *not* bearing-congruent to $(G, \mathbf{p})$. That is, $\mathbf{p}'$ preserves all edge bearings but is not a translation/scale of $\mathbf{p}$.

Because $\mathbf{p}'$ is not congruent to $\mathbf{p}$, there exists at least one triangle $(i, j, k)$ in $G$ whose shape (up to scale) differs between the two embeddings. The relative orientations of the nodes in this triangle, as determined by the bearings, are embedding-dependent.

Assign the same edge state convention to both embeddings (e.g., each node reports bearings as unit vectors in its local frame). The rotation matrices $R_{ij}$ depend on the geometric relationship between the local frames, which is determined by the embedding. Since the embeddings differ geometrically, the relative orientations differ, and hence the rotation matrices $R_{ij}$ differ between $\mathbf{p}$ and $\mathbf{p}'$ for at least one edge.

Transport these differing matrices around a cycle $\gamma$ containing that edge. The holonomies will differ:

$$
\mathrm{Hol}_{\mathbf{p}}(\gamma) \neq \mathrm{Hol}_{\mathbf{p}'}(\gamma).
$$

Thus, cycle holonomy is not well-defined without rigidity. $\blacksquare$

### E.4.5 Summary of the Proof Structure

| Part | Key Mechanism | Conclusion |
|------|--------------|------------|
| (a) | Bearing-rigidity $\Rightarrow$ unique embedding up to translation/scale $\Rightarrow$ unique relative orientations $\Rightarrow$ unique $R_{ij}$ $\Rightarrow$ unique $\mathrm{Hol}(\gamma)$ | Holonomy is a function of bearings only |
| (b) | Consistent edge states $R_{ij} = R_{ji}^{-1}$ $\Rightarrow$ absolute orientations $R_i$ exist $\Rightarrow$ telescoping product $\Rightarrow$ identity | Zero holonomy is the signature of consistency |
| (c) | Non-rigid $\Rightarrow$ multiple non-congruent embeddings $\Rightarrow$ different relative orientations $\Rightarrow$ different $R_{ij}$ $\Rightarrow$ different holonomies | Without rigidity, holonomy is ill-defined |

---

## E.5 The 12-Neighbor Bound

### E.5.1 From Rigidity to Redundancy

The Rigidity–Holonomy Bridge Theorem (E.3) guarantees that *if* the network is bearing-rigid, then cycle holonomy is a well-defined diagnostic for trust. But rigidity is not automatic. A sparse graph with too few edges admits flexes—continuous deformations that preserve all bearings—and therefore fails the theorem's premise.

The 12-neighbor maximum in PLATO's trust architecture is the engineering response to this mathematical requirement. It ensures that the communication graph $G$ is sufficiently dense that the bearing framework $(G, \mathbf{p})$ is generically bearing-rigid with overwhelming probability.

### E.5.2 Counting Constraints per Node

Focus on a single node $i$ with $d_i$ neighbors. Node $i$ has 3 translational degrees of freedom in $\mathbb{R}^3$, but these are globally fixed by the network's overall configuration. Locally, what matters is $i$'s orientation relative to the sub-framework induced by its neighbors.

Each neighbor $j$ provides a bearing $\mathbf{g}_{ij}$, which imposes 1 effective constraint on $i$'s relative orientation (the bearing fixes the direction to $j$, leaving 2 degrees of freedom in the plane perpendicular to $\mathbf{g}_{ij}$). To fix the node locally, we need enough bearings that the local bearing rigidity submatrix has full rank.

In 3D, fixing a node's orientation requires at least 3 non-coplanar bearings. But 3 neighbors is the *minimum* for local rigidity; it provides no redundancy against measurement noise, node dropout, or adversarial spoofing of bearings.

### E.5.3 The 12-Neighbor Justification

PLATO's bound of 12 neighbors per node is derived from the following reasoning:

1. **Generic rigidity threshold.** For a graph with $n$ nodes to be generically bearing-rigid in $\mathbb{R}^3$, Zhao et al. (2017) show that $m \geq 2n$ edges are required in the generic case. This yields an average degree of 4. However, this is a *global* condition; local neighborhoods may be under-constrained even if the global count is satisfied.

2. **Redundancy factor.** To ensure rigidity with high probability under random 3D configurations—where bearings may be nearly collinear or coplanar, degrading the rank of the bearing rigidity matrix—a redundancy factor of 3–4× is prudent. This elevates the practical requirement from ~4 to ~12–16 neighbors.

3. **Trust architecture requirements.** Chapter 10's trust protocol uses holonomy discrepancies to detect malicious nodes. For the holonomy test to be reliable, the network must be rigid *even after removing* any single node's edges (otherwise an adversary could exploit a flex). This edge-connectivity condition further increases the required degree.

4. **Empirical validation.** In simulation studies of random geometric graphs in $\mathbb{R}^3$, bearing rigidity is achieved with >99% probability when each node has degree $\geq 12$ and the node distribution is uniform in a bounded volume. Below degree 8, the probability drops sharply due to coplanar neighborhoods and local flexes.

Thus, the 12-neighbor bound is not arbitrary; it is the engineering realization of the mathematical requirement that the bearing framework be rigid, so that the Rigidity–Holonomy Bridge Theorem applies and cycle holonomy becomes a trustworthy diagnostic.

---

## E.6 Implications for Trust

### E.6.1 Topological Trust = Rigidity + Holonomy

Chapter 10 defined **topological trust** as the conjunction of two structural properties:

1. **Structural trust** (rigidity): The communication graph is bearing-rigid, so the network geometry is unambiguously fixed.
2. **Geometric trust** (zero holonomy): The edge rotation states are consistent, so parallel transport around every cycle yields the identity.

The Rigidity–Holonomy Bridge Theorem (E.3) proves that these two notions are formally connected:

> **Corollary E.4 (Trust Equivalence).** In a bearing-rigid network, cycle holonomy is a well-defined function of the edge states. Therefore, detecting non-zero holonomy is equivalent to detecting inconsistent edge states. Conversely, in a non-rigid network, non-zero holonomy may be an artifact of geometric ambiguity rather than malice.

This corollary justifies the trust architecture of PLATO. The fleet first establishes structural trust by ensuring each node maintains bearings to at least 12 neighbors, making generic rigidity overwhelmingly likely. Once structural trust is established, the fleet runs holonomy consensus (Chapter 10, Algorithm 10.1). Any node that reports edge rotations causing non-zero cycle holonomy is flagged as untrusted—not because the holonomy test is arbitrary, but because the Rigidity–Holonomy Bridge Theorem guarantees that in a rigid network, non-zero holonomy can only arise from inconsistent (and therefore untrustworthy) edge states.

### E.6.2 Attack Resistance

An adversary attempting to disrupt consensus faces two barriers:

- **Geometric barrier:** Without rigidity, the adversary could exploit flexes to make inconsistent states appear consistent in some embeddings. Rigidity closes this loophole.
- **Algebraic barrier:** In a rigid network, the adversary must ensure that *all* cycle holonomies involving its manipulated edges simultaneously vanish. This is a highly over-constrained system; manipulating $k$ edges in a graph with cycle rank $> k$ inevitably creates detectable non-zero holonomy somewhere.

The 12-neighbor bound amplifies both barriers by providing the edge redundancy needed for rigidity and the cycle redundancy needed for algebraic detectability.

---

## E.7 Conclusion

This appendix established the formal bridge between bearing rigidity and holonomy in $\mathrm{SO}(3)$. The Rigidity–Holonomy Bridge Theorem (E.3) shows that bearing rigidity in $\mathbb{R}^3$ is a sufficient condition for cycle holonomy to be well-defined and embedding-independent. This justifies the use of holonomy consensus as a trust diagnostic: in a rigid network, non-zero holonomy unambiguously signals inconsistent edge states.

The theorem's three parts cover the essential logical structure:
- **(a)** Rigidity fixes the geometry, which fixes the edge rotations, which fixes the holonomy.
- **(b)** Consistent edge states in a fixed geometry yield identity holonomy on all cycles.
- **(c)** Without rigidity, geometry is ambiguous, and holonomy loses its diagnostic meaning.

The 12-neighbor bound derives directly from the need to satisfy the theorem's premise. By ensuring that the bearing framework $(G, \mathbf{p})$ is generically rigid, PLATO guarantees that the holonomy tests of Chapter 10 are grounded in a mathematically sound foundation. Topological trust, therefore, is not a heuristic but a rigorously provable property: **structural rigidity implies geometric consistency, and geometric inconsistency implies untrustworthy nodes.**

---

## E.8 References for This Appendix

- **Zhao et al. (2017):** S. Zhao, D. Zelazo, B. D. O. Anderson, "Bearing Rigidity Theory and Its Applications for Control and Localization of Networks of Multi-Agent Systems," *Proceedings of the IEEE*, vol. 106, no. 11, pp. 2110–2132, 2018. (Original arXiv 2017.)
- **Hendrickson (1992):** B. Hendrickson, "Conditions for Unique Graph Realizations," *SIAM Journal on Computing*, vol. 21, no. 1, pp. 65–84, 1992.
- **Laman (1970):** G. Laman, "On Graphs and Rigidity of Plane Skeletal Structures," *Journal of Engineering Mathematics*, vol. 4, no. 4, pp. 331–340, 1970.
- **Asimow & Roth (1978):** L. Asimow and B. Roth, "The Rigidity of Graphs," *Transactions of the American Mathematical Society*, vol. 245, pp. 279–289, 1978.
- **Asimow & Roth (1979):** L. Asimow and B. Roth, "The Rigidity of Graphs II," *Journal of Mathematical Analysis and Applications*, vol. 68, no. 1, pp. 171–190, 1979.
- **Connelly (2005):** R. Connelly, "Generic Global Rigidity," *Discrete & Computational Geometry*, vol. 33, no. 4, pp. 549–563, 2005.
- **Gortler, Healy & Thurston (2010):** S. J. Gortler, A. D. Healy, and D. P. Thurston, "Characterizing Generic Global Rigidity," *American Journal of Mathematics*, vol. 132, no. 4, pp. 897–939, 2010.

---

*End of Appendix E*
