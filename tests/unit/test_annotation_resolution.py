"""Runtime annotation resolution over the public model classes.

The models sit below the client in the import stack: the client mixins
import models at runtime, so the models never import the client back. The
one up-stack name a model annotation may draw on is ``NexarClient`` —
injected here via ``localns`` — and every other name must resolve from the
model module's own imports.
"""

import typing
from types import ModuleType

import pytest

from nexar import models
from nexar.client import NexarClient
from nexar.models import match as match_models


def _exported_classes(module: ModuleType) -> list[type]:
    """Every ``__all__`` export of ``module`` that is a nexar-defined class."""
    classes: list[type] = []
    for name in getattr(module, "__all__", []):
        obj = getattr(module, name, None)
        if isinstance(obj, type) and obj.__module__.startswith("nexar"):
            classes.append(obj)
    return classes


ALL_MODEL_CLASSES = sorted(
    set(_exported_classes(models) + _exported_classes(match_models)),
    key=lambda cls: cls.__name__,
)


@pytest.mark.parametrize("cls", ALL_MODEL_CLASSES, ids=lambda cls: cls.__name__)
def test_model_annotations_resolve_at_runtime(cls: type) -> None:
    """``typing.get_type_hints`` must not NameError on any public model class."""
    typing.get_type_hints(cls, localns={"NexarClient": NexarClient})
