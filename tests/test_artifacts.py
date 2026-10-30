"""Generation owns only its recorded output files."""

import pytest

from plumb.gen.artifacts import write_modules


def test_generation_removes_only_previously_owned_files(tmp_path):
    write_modules({"__init__.py": "first", "enums.py": "obsolete"}, tmp_path)
    (tmp_path / "handwritten.py").write_text("preserve")
    nested = tmp_path / "extension"
    nested.mkdir()
    (nested / "__init__.py").write_text("preserve")
    write_modules({"__init__.py": "second"}, tmp_path)
    assert not (tmp_path / "enums.py").exists()
    assert (tmp_path / "__init__.py").read_text() == "second"
    assert (tmp_path / "handwritten.py").read_text() == "preserve"
    assert (nested / "__init__.py").read_text() == "preserve"


def test_generation_rejects_escaping_filenames(tmp_path):
    with pytest.raises(ValueError, match="invalid generated filename"):
        write_modules({"../outside.py": "bad"}, tmp_path)
