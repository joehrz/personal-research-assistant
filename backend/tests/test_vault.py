from pra.db import init_db, make_engine, make_sessionmaker
from pra.services import vault


def make_session(settings):
    settings.ensure_dirs()
    engine = make_engine(settings.db_path)
    init_db(engine)
    return make_sessionmaker(engine)()


def test_note_roundtrip(settings):
    session = make_session(settings)
    note = vault.create_note(
        session, settings, title="Attention Is All You Need",
        content="Transformers replace recurrence with attention.",
        tags=["ml"], source_url="https://arxiv.org/abs/1706.03762",
    )
    path = settings.vault_dir / note.path
    assert path.exists()
    raw = path.read_text()
    assert raw.startswith("---")
    assert "Attention Is All You Need" in raw
    assert vault.read_content(settings, note) == "Transformers replace recurrence with attention."


def test_untitled_note_takes_first_line(settings):
    session = make_session(settings)
    note = vault.create_note(session, settings, content="# Big Idea\nDetails here.")
    assert note.title == "Big Idea"


def test_update_moves_file_out_of_inbox(settings):
    session = make_session(settings)
    note = vault.create_note(session, settings, content="clip", kind="snippet", inbox=True)
    old_path = settings.vault_dir / note.path
    assert "inbox" in note.path
    vault.update_note(session, settings, note, inbox=False, kind="note", title="Filed note")
    assert "inbox" not in note.path
    assert not old_path.exists()
    assert (settings.vault_dir / note.path).exists()


def test_reindex_picks_up_external_files(settings):
    session = make_session(settings)
    settings.ensure_dirs()
    external = settings.notes_dir / "hand-written.md"
    external.write_text("---\ntitle: Hand written\ntags: [manual]\n---\n\nWritten in vim.\n")
    plain = settings.notes_dir / "plain.md"
    plain.write_text("No frontmatter at all.")
    count = vault.reindex(session, settings)
    assert count == 2
    titles = {n.title for n in session.query(vault.NoteIndex).all()}
    assert "Hand written" in titles
    assert "plain" in titles


def test_reindex_drops_deleted_files(settings):
    session = make_session(settings)
    note = vault.create_note(session, settings, title="Ephemeral", content="x")
    (settings.vault_dir / note.path).unlink()
    vault.reindex(session, settings)
    assert session.get(vault.NoteIndex, note.id) is None


def test_delete_note_removes_file(settings):
    session = make_session(settings)
    note = vault.create_note(session, settings, title="Bye", content="x")
    path = settings.vault_dir / note.path
    vault.delete_note(session, settings, note)
    assert not path.exists()
