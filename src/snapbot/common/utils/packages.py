from __future__ import annotations

from collections.abc import Iterator
from importlib import import_module
from pkgutil import walk_packages
from types import ModuleType

from langchain.tools import BaseTool


def iter_modules(package_name: str) -> Iterator[ModuleType]:
    package = import_module(package_name)

    package_path = getattr(package, "__path__", None)
    if package_path is None:
        raise ValueError(f"{package_name!r} is not a package")

    for module_info in walk_packages(
        package_path,
        prefix=f"{package.__name__}.",
    ):
        if module_info.ispkg:
            continue

        yield import_module(module_info.name)


def iter_builtin_tools(package: str) -> Iterator[BaseTool]:
    seen: set[int] = set()

    for module in iter_modules(package):
        for obj in vars(module).values():
            if not isinstance(obj, BaseTool):
                continue

            obj_id = id(obj)
            if obj_id in seen:
                continue

            seen.add(obj_id)
            yield obj
