"""End-to-end example: register models, request promotions, approve, query lineage."""
from model_registry_pro import (
    ModelRegistry, Model, ModelVersion, Stage, DefaultPolicy,
)


def main() -> None:
    print("=" * 60)
    print("  MODEL-REGISTRY-PRO :: APPROVAL WORKFLOW DEMO")
    print("=" * 60)

    # Set up registry with two designated approvers
    registry = ModelRegistry(policy=DefaultPolicy(approvers={"alice", "bob"}))

    # Register lineage: rag-agent v1 -> v2 (fine-tuned) -> v3 (RLHF'd)
    v1 = Model(
        version=ModelVersion("rag-agent", "1.0.0"),
        description="initial RAG agent over docs corpus",
        created_by="dev1",
        metadata={"params": "1.5B", "training_corpus": "docs-2024-q3"},
    )
    v2 = Model(
        version=ModelVersion("rag-agent", "2.0.0"),
        description="fine-tuned on customer Q&A logs",
        parent=v1.version,
        created_by="dev2",
        metadata={"params": "1.5B", "training_corpus": "customer-qa-2024-q4"},
    )
    v3 = Model(
        version=ModelVersion("rag-agent", "3.0.0"),
        description="RLHF over v2 with thumbs-up feedback",
        parent=v2.version,
        created_by="dev3",
        metadata={"params": "1.5B", "rlhf_episodes": 50000},
    )
    for m in (v1, v2, v3):
        registry.register(m)

    print(f"\n[1/4] Registered 3 model versions:")
    for m in registry.list_versions("rag-agent"):
        print(f"      {m.version} ({m.description})")

    # Promote v3 through DEV -> STAGING (auto, no approval) -> PROD (gated)
    print(f"\n[2/4] Promoting rag-agent:3.0.0 DEV -> STAGING (auto-approved)...")
    auto = registry.request_promotion(v3.version, Stage.STAGING, requested_by="dev3")
    print(f"      Status: {auto.state.value} | Stage: {registry.stage_of(v3.version).value}")

    print(f"\n[3/4] Requesting STAGING -> PROD (requires approval)...")
    pending = registry.request_promotion(
        v3.version, Stage.PROD, requested_by="dev3",
        notes="passed eval suite, latency p95 = 380ms"
    )
    print(f"      Approval id={pending.id} | State: {pending.state.value}")
    print(f"      Stage frozen at: {registry.stage_of(v3.version).value}")
    print(f"      Pending queue size: {len(registry.pending_approvals())}")

    print(f"\n[4/4] Alice approves...")
    approved = registry.approve(pending.id, approved_by="alice", notes="reviewed metrics, ship it")
    print(f"      Final state: {approved.state.value} by {approved.decided_by}")
    print(f"      Stage now: {registry.stage_of(v3.version).value.upper()}")

    # Lineage query
    print(f"\nLineage of rag-agent:3.0.0:")
    for ancestor in registry.ancestors(v3.version):
        print(f"      <- {ancestor.version}")

    # Production lookup
    prod = registry.production_version("rag-agent")
    print(f"\nCurrent production version: {prod.version if prod else 'none'}")

    print("\n" + "=" * 60)
    print("  WORKFLOW COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
