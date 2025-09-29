from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agi_mindloop.memory.meta_store import MetaStore


def _make_store(tmp_path):
    store = MetaStore(str(tmp_path / "meta.db"))
    cur = store.conn.cursor()
    cur.execute(
        "INSERT INTO cycles(started_at, ended_at, seed, config_hash) VALUES(?,?,?,?)",
        ("start", "end", 0, "hash"),
    )
    cycle_id = cur.lastrowid
    store.conn.commit()
    return store, int(cycle_id)


def test_get_artifacts_text_accepts_generator(tmp_path):
    store, cycle_id = _make_store(tmp_path)
    try:
        content = "artifact content"
        artifact_id = store.add_artifact(cycle_id, "note", content, "now")
        id_gen = (i for i in [artifact_id])

        result = store.get_artifacts_text(id_gen)

        assert result == {artifact_id: content}
    finally:
        store.close()


def test_get_artifacts_text_empty_input_returns_empty_dict(tmp_path):
    store, _ = _make_store(tmp_path)
    try:
        result = store.get_artifacts_text([])

        assert result == {}
    finally:
        store.close()
