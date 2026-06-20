from importlib.machinery import SourceFileLoader
import os

HERE = os.path.dirname(__file__)
module_path = os.path.abspath(os.path.join(HERE, '..', 'dira-nuriot', 'validate_data.py'))
val = SourceFileLoader('validate_data', module_path).load_module()


def test_validate_permissive():
    # permissive mode should return True (warnings OK)
    ok = val.validate_all(base_dir=os.path.abspath(os.path.join(HERE, '..', 'dira-nuriot')), strict=False)
    assert ok is True


def test_validate_strict():
    ok = val.validate_all(base_dir=os.path.abspath(os.path.join(HERE, '..', 'dira-nuriot')), strict=True)
    assert ok is True
