"""Bounded native sampling with explicit acceleration and timeout provenance.

sample_native returns (pair, metadata). Call it directly, not inside a two-second
runtime.call: it owns its bounded attempts. SamplerTimeout.metadata records each
failed attempt. No output labels are examined to choose a sample or retry.
"""
from contextlib import contextmanager
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import tempfile
import time
import numpy as np
from .runtime import call

SLOW_FAMILIES = frozenset({'1b8318e3', '985ae207', 'bd14c3bf', 'f3b10344'})
SAMPLER_985_SHA256 = 'd5d77dbfaf556204a345b8e67df783f241f7b2da6a887eaebacc94c745de7fef'
NATIVE_985_SHA256 = '5707648d96eac485e2dc9d319edf38c9519ca3bc54ab77a76704a3515f33ac64'

class SamplerTimeout(TimeoutError):
    def __init__(self, metadata):
        self.metadata = metadata
        super().__init__(f"{metadata['task_id']}: sampler timed out; seed={metadata['seed']}; "
                         f"limits={[x['limit_seconds'] for x in metadata['attempts']]}")

class SamplingSetupError(RuntimeError):
    pass


def timeout_limits(task_id):
    """Finite policy, not a guarantee that every native rejection loop finishes."""
    # The complete 1b audit has p95 89 s, p99 161 s, maximum 284 s.
    if task_id == '1b8318e3':
        return (5.0, 30.0, 300.0)
    return (5.0, 30.0) if task_id in SLOW_FAMILIES else (5.0,)


@contextmanager
def _seeded_rng(seed):
    py_state, np_state = random.getstate(), np.random.get_state()
    random.seed(seed)
    np.random.seed(seed % (2**32))
    try:
        yield
    finally:
        random.setstate(py_state)
        np.random.set_state(np_state)


def prepare_compiled_985():
    """Build the already-audited source once per host; never download a binary."""
    source = Path(__file__).with_name('audit_support') / 'task_985ae207_parameter_sampler.cpp'
    if hashlib.sha256(source.read_bytes()).hexdigest() != SAMPLER_985_SHA256:
        raise SamplingSetupError('985ae207 compiled source hash differs from audited source')
    compiler = shutil.which('c++') or shutil.which('g++')
    if not compiler:
        raise SamplingSetupError('No C++ compiler available; native fallback required')
    try:
        version = subprocess.run([compiler, '--version'], capture_output=True, text=True,
                                 check=True, timeout=10).stdout.splitlines()[0]
    except (OSError, subprocess.SubprocessError) as exc:
        raise SamplingSetupError('C++ compiler unavailable: ' + repr(exc)) from exc
    key = hashlib.sha256(json.dumps([SAMPLER_985_SHA256, platform.system(),
                                    platform.machine(), compiler, version]).encode()).hexdigest()
    cache = Path(os.environ.get('ARCGEN_SAMPLER_CACHE', str(Path(tempfile.gettempdir()) / ('arcgen-pool-samplers-' + str(os.getuid())))))
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    binary = cache / ('985ae207-' + key)
    if not binary.exists():
        fd, name = tempfile.mkstemp(prefix='compile-985-', dir=cache)
        os.close(fd)
        temporary = Path(name)
        try:
            subprocess.run([compiler, '-O3', '-std=c++17', str(source), '-o', str(temporary)],
                           capture_output=True, text=True, check=True, timeout=60)
            temporary.chmod(0o700)
            os.replace(temporary, binary)
        except (OSError, subprocess.SubprocessError) as exc:
            raise SamplingSetupError('C++ sampler build failed: ' + repr(exc)) from exc
        finally:
            temporary.unlink(missing_ok=True)
    return binary, {'sampler_source_sha256': SAMPLER_985_SHA256,
                    'sampler_binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
                    'compiler': version}


def _compiled_985(native, seed, metadata):
    source = inspect.getsourcefile(native)
    if source is None or hashlib.sha256(Path(source).read_bytes()).hexdigest() != NATIVE_985_SHA256:
        raise SamplingSetupError('985ae207 native constructor hash differs from audited renderer')
    binary, build = prepare_compiled_985()
    derived_seed = int.from_bytes(hashlib.sha256(f'985ae207:{seed}:mt19937-v1'.encode()).digest()[:4], 'big')
    metadata.update(build, mode='compiled_parameter_sampler', rng='C++ mt19937 via std uniform distributions; different stream from Python',
                    derived_seed=derived_seed, native_seed_equivalent=False,
                    native_constructor_sha256=NATIVE_985_SHA256,
                    sampling_scope='Audited uniform parameter proposal law and native acceptance checks; explicit native renderer generates labels.')
    for limit in timeout_limits('985ae207'):
        started = time.monotonic()
        attempt = {'limit_seconds': limit, 'mode': metadata['mode']}
        try:
            result = subprocess.run([str(binary), '1', str(derived_seed)], capture_output=True,
                                    text=True, check=True, timeout=limit)
            raw = json.loads(result.stdout)
            if raw.get('_seed') != derived_seed:
                raise RuntimeError('Compiled sampler returned an unexpected seed')
            params = {k:v for k,v in raw.items() if not k.startswith('_')}
            # Explicit parameters avoid rejection sampling in native.generate.
            with _seeded_rng(seed):
                pair = call(native, seconds=5, **params)
            attempt.update(status='success', elapsed_seconds=time.monotonic()-started)
            metadata['attempts'].append(attempt)
            metadata.update(proposal_attempts=raw['_attempts'], explicit_parameters=params)
            return pair, metadata
        except (subprocess.TimeoutExpired, TimeoutError):
            attempt.update(status='timeout', elapsed_seconds=time.monotonic()-started)
            metadata['attempts'].append(attempt)
    raise SamplerTimeout(metadata)


def sample_native(task_id, native, seed, parameters=None, *, use_compiled=True):
    """Sample once, retrying the same seeded draw only after a timeout.

    Explicit parameter requests use the native path. Compilation failures fall
    back visibly; sampler execution errors propagate rather than masquerading
    as intrinsic ambiguity. Both caller RNG states are restored on every exit.
    """
    parameters = dict(parameters or {})
    metadata = {'task_id': task_id, 'seed': int(seed), 'parameters': parameters,
                'mode': 'native', 'attempts': [], 'native_seed_equivalent': True}
    if task_id == '985ae207' and not parameters and use_compiled:
        try:
            return _compiled_985(native, seed, metadata)
        except SamplingSetupError as exc:
            metadata['compiled_fallback_reason'] = str(exc)
    for limit in timeout_limits(task_id):
        started = time.monotonic()
        attempt = {'limit_seconds': limit, 'mode': 'native'}
        try:
            with _seeded_rng(seed):
                pair = call(native, seconds=limit, **parameters)
            attempt.update(status='success', elapsed_seconds=time.monotonic()-started)
            metadata['attempts'].append(attempt)
            return pair, metadata
        except TimeoutError:
            attempt.update(status='timeout', elapsed_seconds=time.monotonic()-started)
            metadata['attempts'].append(attempt)
    raise SamplerTimeout(metadata)

RAW_1B_POOL_SHA256 = '7d58c8f42063b13cabcda1f257790cb8187118864c87d76c30c18e4f5de2529a'
NATIVE_1B_SHA256 = '8b11ded6b66197c05b2946501a13dfda158ecec05f1be0eb6344559a8b94219f'


def load_native_seed_pool(task_id, native):
    """Return the complete archived raw stream, including ambiguous cases.

    This is reusable data, not 1,150 newly generated samples. Old gate status is
    provenance only; production input-only evidence gates still decide eligibility.
    """
    if task_id != '1b8318e3':
        return [], None
    source = inspect.getsourcefile(native)
    if source is None or hashlib.sha256(Path(source).read_bytes()).hexdigest() != NATIVE_1B_SHA256:
        raise SamplingSetupError('1b8318e3 native constructor differs from archived raw stream')
    path = Path(__file__).with_name('audit_support') / 'task_1b8318e3_raw_pool.jsonl'
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != RAW_1B_POOL_SHA256:
        raise SamplingSetupError('1b8318e3 raw stream hash mismatch')
    records = sorted((json.loads(line) for line in payload.splitlines()), key=lambda r:r['index'])
    if [r['index'] for r in records] != list(range(1150)):
        raise SamplingSetupError('1b8318e3 raw stream is not complete indices 0..1149')
    for record in records:
        expected = int(hashlib.sha256(f"factory-fresh-1b8318e3:{record['index']}".encode()).hexdigest()[:12], 16)
        if record['seed'] != expected or 'pair' not in record:
            raise SamplingSetupError('1b8318e3 raw stream seed/pair is missing or mismatched')
    metadata = {'mode':'archived_raw_native_stream', 'path':'arc_agi2/audit_support/task_1b8318e3_raw_pool.jsonl',
                'sha256':RAW_1B_POOL_SHA256, 'native_constructor_sha256':NATIVE_1B_SHA256,
                'record_count':len(records), 'complete_index_range':[0,1149],
                'status_is_provenance_only':True, 'fresh_draws_this_job':False}
    return records, metadata


def family_budget_seconds(task_id, configured_default):
    """Finite family budgets; callers must report quota shortfalls explicitly."""
    override = os.environ.get('ARCGEN_FAMILY_SECONDS_' + task_id.upper())
    if override is not None:
        value = int(override)
        if value <= 0:raise ValueError('Family sampling budget must be positive')
        return value
    floor = {'1b8318e3':3600, '985ae207':1800, 'bd14c3bf':3600, 'f3b10344':1800}.get(task_id,0)
    return max(int(configured_default),floor)
