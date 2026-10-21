"""Auditable metadata for explicitly versioned synthetic family definitions."""
import hashlib
import importlib
from pathlib import Path


def variant_provenance(task_id):
    if task_id != 'a64e4611':
        return None
    module = importlib.import_module('tasks.task_' + task_id)
    metadata = dict(module.SYNTHETIC_VARIANT)
    metadata['constructor_parameters'] = dict(metadata['constructor_parameters'])
    metadata['constructor_sha256'] = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
    return metadata
