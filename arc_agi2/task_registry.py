"""Reviewed standalone additions; upstream's 900 entries remain unchanged."""
import importlib

NEW_TASK_IDS=('009d5c81', '0a2355a6', '135a2760', '16de56c4', '1818057f', '2de01db2', '3194b014', '423a55dc', '45a5af55', '505fff84', '62593bfd', '97d7923e')

def additions():
    result={}
    for tid in NEW_TASK_IDS:
        module=importlib.import_module('tasks.task_'+tid)
        result[tid]=[module.generate,module.validate]
    return result
