import pytest
from tutor_engine import run_python,test_submission as evaluate_submission,SafetyError
def test_success(): assert evaluate_submission("print(5)",[{"expected":"5"}])["passed"]==1
def test_wrong(): assert evaluate_submission("print(4)",[{"expected":"5"}])["passed"]==0
def test_import_blocked():
    with pytest.raises(SafetyError): run_python("import os")
def test_timeout(): assert run_python("while True: pass",1)["status"]=="timeout"
