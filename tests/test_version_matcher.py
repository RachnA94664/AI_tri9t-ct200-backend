import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.document import DocumentVersion, Node
from app.services.version_matcher import match_nodes, ChangeStatus


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def make_node(db, version_id, number, text, body, order):
    import hashlib
    node = Node(
        document_version_id=version_id,
        parent_id=None,
        heading_number=number,
        heading_text=text,
        level=number.count(".") + 1 if number else 0,
        body_text=body,
        content_hash=hashlib.sha256(body.encode()).hexdigest(),
        order_index=order,
    )
    db.add(node)
    db.flush()
    return node


def test_identical_node_is_unchanged(db_session):
    v1 = DocumentVersion(label="v1", source_filename="v1.pdf")
    v2 = DocumentVersion(label="v2", source_filename="v2.pdf")
    db_session.add_all([v1, v2])
    db_session.flush()

    make_node(db_session, v1.id, "5.1", "Local Storage", "stores up to 100 readings", 0)
    make_node(db_session, v2.id, "5.1", "Local Storage", "stores up to 100 readings", 0)
    db_session.commit()

    results = match_nodes(db_session, v1.id, v2.id)
    matched = [r for r in results if r.match_method == "heading_number"]
    assert len(matched) == 1
    assert matched[0].status == ChangeStatus.UNCHANGED


def test_changed_body_text_is_flagged(db_session):
    v1 = DocumentVersion(label="v1", source_filename="v1.pdf")
    v2 = DocumentVersion(label="v2", source_filename="v2.pdf")
    db_session.add_all([v1, v2])
    db_session.flush()

    make_node(db_session, v1.id, "3.2", "Cuff Inflation Sequence", "40 mmHg increments", 0)
    make_node(db_session, v2.id, "3.2", "Cuff Inflation Sequence", "30 mmHg increments", 0)
    db_session.commit()

    results = match_nodes(db_session, v1.id, v2.id)
    result = [r for r in results if r.v2_node and r.v2_node.heading_number == "3.2"][0]
    assert result.status == ChangeStatus.CHANGED
    assert result.match_method == "heading_number"


def test_new_node_with_no_v1_match(db_session):
    """E6 error code row in v2 with no v1 counterpart."""
    v1 = DocumentVersion(label="v1", source_filename="v1.pdf")
    v2 = DocumentVersion(label="v2", source_filename="v2.pdf")
    db_session.add_all([v1, v2])
    db_session.flush()

    make_node(db_session, v1.id, "4.2", "Error Codes", "E1-E5 table", 0)
    make_node(db_session, v2.id, "4.2", "Error Codes", "E1-E6 table", 0)
    make_node(db_session, v2.id, "4.2.1", "E6 Bluetooth Sync Failure", "new row detail", 1)
    db_session.commit()

    results = match_nodes(db_session, v1.id, v2.id)
    new_nodes = [r for r in results if r.status == ChangeStatus.NEW]
    assert len(new_nodes) == 1
    assert new_nodes[0].v2_node.heading_number == "4.2.1"


def test_adversarial_renamed_and_renumbered_node_misclassifies(db_session):
    """
    ADVERSARIAL CASE: a node whose heading_number AND heading_text both
    change between versions is indistinguishable from 'old one removed,
    new one added' — there is no signal left to link them. This test
    documents that the system gets this WRONG, on purpose, rather than
    hiding the limitation.
    """
    v1 = DocumentVersion(label="v1", source_filename="v1.pdf")
    v2 = DocumentVersion(label="v2", source_filename="v2.pdf")
    db_session.add_all([v1, v2])
    db_session.flush()

    make_node(db_session, v1.id, "5.2", "Bluetooth Sync", "pairs via BLE", 0)
    # Same logical section, but renumbered to 5.3 AND retitled in v2
    make_node(db_session, v2.id, "5.3", "Wireless Pairing", "pairs via BLE and NFC", 0)
    db_session.commit()

    results = match_nodes(db_session, v1.id, v2.id)
    statuses = {r.status for r in results}
    # We EXPECT this to be misclassified as REMOVED + NEW, not CHANGED —
    # asserting the known limitation, not a desired behavior.
    assert ChangeStatus.REMOVED in statuses
    assert ChangeStatus.NEW in statuses
    assert ChangeStatus.CHANGED not in statuses