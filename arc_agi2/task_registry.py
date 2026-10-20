"""Reviewed standalone additions; upstream's 900 entries remain unchanged."""
import importlib

NEW_TASK_IDS=('135a2760','16de56c4','62593bfd')

def additions():
    result={}
    for tid in NEW_TASK_IDS:
        module=importlib.import_module('tasks.task_'+tid)
        result[tid]=[module.generate,module.validate]
    return result
