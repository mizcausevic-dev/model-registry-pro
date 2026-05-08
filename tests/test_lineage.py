from model_registry_pro import ModelRegistry, Model, ModelVersion
from model_registry_pro.policy import OpenPolicy


def test_simple_lineage_chain():
    r = ModelRegistry(policy=OpenPolicy())
    v1 = Model(version=ModelVersion("agent", "1.0"))
    v2 = Model(version=ModelVersion("agent", "2.0"), parent=v1.version)
    v3 = Model(version=ModelVersion("agent", "3.0"), parent=v2.version)
    r.register(v1)
    r.register(v2)
    r.register(v3)

    ancestors = r.ancestors(v3.version)
    assert [str(m.version) for m in ancestors] == ["agent:2.0", "agent:1.0"]


def test_descendants_branching():
    r = ModelRegistry(policy=OpenPolicy())
    base = Model(version=ModelVersion("base", "1.0"))
    fork_a = Model(version=ModelVersion("fork-a", "1.0"), parent=base.version)
    fork_b = Model(version=ModelVersion("fork-b", "1.0"), parent=base.version)
    grandchild = Model(version=ModelVersion("fork-a", "1.1"), parent=fork_a.version)
    r.register(base)
    r.register(fork_a)
    r.register(fork_b)
    r.register(grandchild)

    desc = r.descendants(base.version)
    assert len(desc) == 3
    names = {str(m.version) for m in desc}
    assert names == {"fork-a:1.0", "fork-b:1.0", "fork-a:1.1"}


def test_no_parent_no_ancestors():
    r = ModelRegistry(policy=OpenPolicy())
    m = Model(version=ModelVersion("solo", "1.0"))
    r.register(m)
    assert r.ancestors(m.version) == []
    assert r.descendants(m.version) == []


def test_lineage_graph_direct_access():
    r = ModelRegistry(policy=OpenPolicy())
    parent = Model(version=ModelVersion("p", "1.0"))
    child = Model(version=ModelVersion("c", "1.0"), parent=parent.version)
    r.register(parent)
    r.register(child)

    graph = r.lineage()
    assert graph.parent_of(child.version) == parent.version
    assert child.version in graph.children_of(parent.version)
