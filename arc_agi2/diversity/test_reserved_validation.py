"""Prior-stage validation protection must fail closed on invalid/stale ledgers."""
import hashlib
import json
import pytest
from arc_agi2.diversity.prepare import reserved_validation_orbits


def test_orbit_ledger_exact_membership_and_integrity(tmp_path):
    p = tmp_path / 'orbits.json'
    a, b = 'a' * 64, 'b' * 64
    p.write_text(json.dumps([a, b, a]))
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    assert reserved_validation_orbits(str(p), digest) == {a, b}
    p.write_text(json.dumps(['c' * 64]))
    reserved_validation_orbits.cache_clear()
    with pytest.raises(ValueError, match='changed'):
        reserved_validation_orbits(str(p), digest)


@pytest.mark.parametrize('value', [{}, [1], ['no'], ['g' * 64]])
def test_invalid_ledger_rejected(tmp_path, value):
    p = tmp_path / 'invalid.json'
    p.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='JSON list'):
        reserved_validation_orbits(str(p), hashlib.sha256(p.read_bytes()).hexdigest())
