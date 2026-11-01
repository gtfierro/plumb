"""Constructive SHACL value constraints shared by generated configurations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .errors import ModelingError
from .relations import _collection

if TYPE_CHECKING:
    from .entity import Entity


@dataclass(frozen=True)
class ShapeValues:
    """Required members, defaults, choices, and cardinality for one predicate."""

    name: str
    source_shape: str
    required: tuple[Any, ...] = ()
    defaults: tuple[Any, ...] = ()
    choices: tuple[Any, ...] | None = None
    minimum: int = 0
    maximum: int | None = None


def constraints(cls: type[Entity]) -> tuple[ShapeValues, ...]:
    # The compiler emits effective constraints, including semantic parents
    # omitted by Python's MRO. Runtime inheritance must not compose them again.
    return cls._shape_constraints


def initial_values(entity: Entity, supplied: dict[str, Any]) -> dict[str, Any]:
    # Supplied values replace defaults; sh:hasValue members still accumulate.
    # Apply this merge only during construction, never during hydration.
    values = dict(supplied)
    specs = entity._effective_specs()
    for item in constraints(type(entity)):
        spec = specs[item.name]
        required = [_resolve(entity, spec.kind, value) for value in item.required]
        current = values.get(item.name)
        if current is None and item.defaults:
            current = tuple(
                _resolve(entity, spec.kind, value) for value in item.defaults
            )
        if current is None and not required:
            continue
        many = spec.kind in {"object", "class", "enum"} and spec.max_count != 1
        if current is None:
            current = ()
        if many:
            current = _collection(entity, spec, current)
            keys = {_key(value) for value in current}
            for value in required:
                if _key(value) not in keys:
                    current.append(value)
                    keys.add(_key(value))
        else:
            if isinstance(current, tuple):
                current = current[0] if current else None
            if current is None and required:
                current = required[0]
        if current is not None:
            values[item.name] = current
    return values


def check_values(entity: Entity, name: str, value: object) -> None:
    specs = entity._effective_specs()
    spec = specs.get(name)
    if spec is None:
        return
    many = spec.kind in {"object", "class", "enum"} and spec.max_count != 1
    values = (
        _collection(entity, spec, value) if many else ([] if value is None else [value])
    )
    for item in constraints(type(entity)):
        if item.name != name:
            continue
        keys = {_key(value) for value in values}
        if any(_key(required) not in keys for required in item.required):
            raise ModelingError(
                f"{entity.name}.{name}: missing sh:hasValue member ({item.source_shape})"
            )
        if item.choices is not None and any(
            _key(value) not in {_key(choice) for choice in item.choices}
            for value in values
        ):
            raise ModelingError(
                f"{entity.name}.{name}: value is outside sh:in ({item.source_shape})"
            )
        # Minima belong to constructor completion and graph validation. Edits
        # may temporarily remove an endpoint while rerouting a connection.
        if item.maximum is not None and len(values) > item.maximum:
            raise ModelingError(
                f"{entity.name}.{name}: violates shape cardinality ({item.source_shape})"
            )


def _resolve(entity: Entity, kind: str, value: Any) -> Any:
    from .terms import TermValue

    if isinstance(value, TermValue):
        registry = entity.meta.registry
        if kind == "class":
            try:
                return registry.by_iri[value.iri]
            except KeyError:
                raise ModelingError(
                    f"{entity.name}: unlinked class default {value.iri}"
                ) from None
        if kind == "enum":
            return registry.resolve_enum(value.iri)
    return value


def _key(value: Any) -> Any:
    from .entity import Entity

    if isinstance(value, type) and issubclass(value, Entity):
        return ("iri", value.meta.iri)
    if isinstance(value, Entity):
        return ("iri", value.meta.instance_iri)
    if hasattr(value, "iri"):
        return ("iri", value.iri)
    if isinstance(value, bool):
        return ("bool", value)
    return ("literal", value)
