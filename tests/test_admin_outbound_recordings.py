import importlib.util

import pytest

# admin_ui backend imports fastapi at module load. Skip the whole module on
# environments that don't have it (CI's engine-only jobs run without admin_ui
# deps), matching tests/test_admin_call_recordings.py.
if importlib.util.find_spec("fastapi") is None:
    pytest.skip("fastapi not installed; admin_ui outbound tests skipped", allow_module_level=True)

from admin_ui.backend.api import outbound


def test_media_ulaw_lookup_only_relaxes_extension_case(tmp_path, monkeypatch):
    upper_dir = tmp_path / "upper"
    lower_dir = tmp_path / "lower"
    upper_dir.mkdir()
    lower_dir.mkdir()

    monkeypatch.setattr(outbound, "_media_dir", lambda: str(upper_dir))
    promo_upper = upper_dir / "Promo.ULAW"
    promo_upper.write_bytes(b"upper")

    assert outbound._find_media_ulaw_path("Promo") == str(promo_upper)
    assert outbound._read_media_ulaw("sound:ai-generated/Promo") == b"upper"
    assert outbound._find_media_ulaw_path("promo") is None

    monkeypatch.setattr(outbound, "_media_dir", lambda: str(lower_dir))
    promo_lower = lower_dir / "promo.ulaw"
    promo_lower.write_bytes(b"lower")

    assert outbound._find_media_ulaw_path("promo") == str(promo_lower)
    assert outbound._read_media_ulaw("sound:ai-generated/promo") == b"lower"


@pytest.mark.asyncio
async def test_list_recordings_includes_uppercase_ulaw_suffix(tmp_path, monkeypatch):
    monkeypatch.setattr(outbound, "_media_dir", lambda: str(tmp_path))
    (tmp_path / "Greeting.ULAW").write_bytes(b"abc")
    (tmp_path / "notes.txt").write_text("ignore")

    rows = await outbound.list_recordings()

    assert len(rows) == 1
    assert rows[0].filename == "Greeting.ULAW"
    assert rows[0].media_uri == "sound:ai-generated/Greeting"
    assert rows[0].size_bytes == 3
