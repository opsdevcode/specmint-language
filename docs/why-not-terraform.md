# Why Mint is not Terraform / HCL

Mint is a governed automation **language**. Terraform is an
infrastructure provisioner organized around resources, providers, CRUD,
apply, and a state file.

Mint's public terms are intent, capability, target, integration,
realization, observation, plan, approval, executor, verification,
evidence, and outcome (ADR 018).

| Terraform-shaped idea | Mint |
| --- | --- |
| Resource as the center | Capability + target + integration realization |
| Provider CRUD | Observation, plan, then a separate executor |
| `apply` | Absent. `mint apply` is not a command |
| State file | Lifecycle records, verification, evidence, outcomes |
| Plan implies apply rights | Planning never grants execution authority |

An integration that can plan does not gain execution authority. SpecMint
owns governed lifecycle coherence. Product domains (Repave, Overpass,
Toll, Dispatch) keep their own capability semantics.

See [Integration Protocol v0](../specification/mint/v0/integration-protocol.md)
and [ADR 018](adr/018-mint-integration-terminology.md).
