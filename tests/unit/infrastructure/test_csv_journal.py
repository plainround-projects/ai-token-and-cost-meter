import pytest

from tests.conftest import row
from token_meter.domain.llm import StopReason
from token_meter.infrastructure.csv_journal import COLUMNS, CsvJournal, JournalCorrupt


def test_a_new_journal_gets_one_header_and_no_rows(tmp_path):
    journal = CsvJournal(tmp_path / "out" / "j.csv")
    assert journal.rows() == []
    assert (tmp_path / "out" / "j.csv").read_text().strip() == ",".join(COLUMNS)


def test_rows_survive_a_reopen_and_the_header_is_not_written_twice(tmp_path):
    path = tmp_path / "j.csv"
    journal = CsvJournal(path)
    journal.append(row("a", "t0", 0, 30, 5, 'hello, "world"\nsecond line'))
    journal.append(row("a", "t0", 1, 30, 6, "ça va", StopReason.LENGTH))
    reopened = CsvJournal(path)
    assert [r.text for r in reopened.rows()] == ['hello, "world"\nsecond line', "ça va"]
    assert reopened.rows()[1].stop_reason is StopReason.LENGTH
    assert path.read_text().count("prompt_id,setting") == 1
    assert {k.repeat for k in reopened.done_keys()} == {0, 1}


def test_a_torn_last_line_from_a_kill_is_cut_off_on_open(tmp_path):
    path = tmp_path / "j.csv"
    journal = CsvJournal(path)
    journal.append(row("a", "t0", 0, 30, 5))
    with path.open("a") as handle:
        handle.write("a,t0,1,30,")  # the process died in the middle of this row
    reopened = CsvJournal(path)
    assert len(reopened.rows()) == 1
    reopened.append(row("a", "t0", 1, 30, 5))
    assert len(CsvJournal(path).rows()) == 2


def test_a_file_without_the_header_is_reported_not_misread(tmp_path):
    path = tmp_path / "j.csv"
    path.write_text('a,t0,0,1,1,stop,0.1,"x"\n')
    with pytest.raises(JournalCorrupt, match="expected the header"):
        CsvJournal(path)
