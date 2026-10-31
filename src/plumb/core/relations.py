"""Typed descriptors that back generated attributes.

Three descriptor flavors cover the SHACL cardinality/kind matrix:

- :class:`Rel` — object property, unbounded: ``ahu.feeds`` is a
  :class:`RelSet` you ``.add()`` to.
- :class:`RelOne` — object property with ``maxCount 1``: plain attribute
  holding an entity or ``None``.
- :class:`Lit` — datatype property with ``maxCount 1``: plain attribute
  holding a Python literal or ``None``.

The descriptors carry a :class:`~plumb.core.meta.PropertySpec` and perform
runtime range checks that mirror what a static type checker enforces from the
generated annotations — so users who don't run a checker still get immediate,
readable errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Iterable, Iterator, TypeVar, overload

from .errors import RangeError
from .meta import PropertySpec

if TYPE_CHECKING:
    from .entity import Entity

T = TypeVar("T")
#: Literal values are plain Python objects, not entities.
V = TypeVar("V")


class RelSet(Generic[T]):
    """Live, ordered, duplicate-free set of links from one entity.

    Obtained by accessing a :class:`Rel` attribute on an instance
    (``ahu.feeds``). Mutations write through to the model immediately and
    keep the inverse property (if one exists) in sync.
    """

    __slots__ = ("_owner", "_spec", "_items")

    def __init__(self, owner: Entity, spec: PropertySpec) -> None:
        self._owner = owner
        self._spec = spec
        self._items: list[T] = []

    def _replace(self, items: Iterable[T]) -> None:
        """Validate the complete update before touching either side of an edge."""
        owner, spec = self._owner, self._spec
        owner._model._assert_mutable()
        proposed = list(dict.fromkeys(_link_value(spec, item) for item in items))
        for item in proposed:
            owner._check_range(spec, item)
        _check_maximum(owner, spec, len(proposed))
        if owner._shape_constraints:
            from .shape_constraints import check_values

            check_values(owner, spec.name, proposed)
        added = [item for item in proposed if item not in self._items]
        removed = [item for item in self._items if item not in proposed]
        if spec.kind == "object":
            for item in added:
                _check_inverse(owner, spec, item)
            for item in removed:
                _unlink_inverse(owner, spec, item)
            for item in added:
                _link_inverse(owner, spec, item)
        self._items[:] = proposed
        if added or removed:
            owner._model._touch(owner, *added, *removed)

    def add(self, *items: T) -> None:
        """Link target entities atomically. Duplicates are ignored."""
        self._replace([*self._items, *items])

    def remove(self, item: T) -> None:
        """Unlink a target entity and its mirrored inverse edge."""
        proposed = list(self._items)
        proposed.remove(item)
        self._replace(proposed)

    def clear(self) -> None:
        """Unlink everything as one update."""
        self._replace([])

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, item: object) -> bool:
        return item in self._items

    def __repr__(self) -> str:
        return f"RelSet({self._spec.name}={list(self._items)!r})"


class Rel(Generic[T]):
    """Descriptor for an unbounded object property.

    Generated code declares ``feeds: Rel[Equipment] = Rel(_P_feeds)``; the
    annotation gives type checkers ``RelSet[Equipment]`` on read and
    ``Iterable[Equipment]`` on assignment.
    """

    def __init__(self, spec: PropertySpec) -> None:
        self.spec = spec

    def __set_name__(self, owner: type, name: str) -> None:
        if name != self.spec.name:  # pragma: no cover - generator invariant
            raise TypeError(
                f"attribute {name!r} does not match spec name {self.spec.name!r}"
            )

    @overload
    def __get__(self, obj: None, owner: type) -> Rel[T]: ...
    @overload
    def __get__(self, obj: Entity, owner: type) -> RelSet[T]: ...

    def __get__(self, obj: Entity | None, owner: type) -> Rel[T] | RelSet[T]:
        if obj is None:
            return self
        return obj._store_for(self.spec)

    def __set__(self, obj: Entity, value: Iterable[T]) -> None:
        """Replace the full contents (used by constructor kwargs)."""
        obj._store_for(self.spec)._replace(_collection(obj, self.spec, value))


class RelOne(Generic[T]):
    """Descriptor for an object property with ``maxCount 1``."""

    def __init__(self, spec: PropertySpec) -> None:
        self.spec = spec

    def __set_name__(self, owner: type, name: str) -> None:
        if name != self.spec.name:  # pragma: no cover - generator invariant
            raise TypeError(
                f"attribute {name!r} does not match spec name {self.spec.name!r}"
            )

    @overload
    def __get__(self, obj: None, owner: type) -> RelOne[T]: ...
    @overload
    def __get__(self, obj: Entity, owner: type) -> T | None: ...

    def __get__(self, obj: Entity | None, owner: type) -> RelOne[T] | T | None:
        if obj is None:
            return self
        return obj._data.get(self.spec.name)

    def __set__(self, obj: Entity, value: T | None) -> None:
        obj._model._assert_mutable()
        if value is not None:
            value = _link_value(self.spec, value)
            obj._check_range(self.spec, value)
        _check_scalar(obj, self.spec, value)
        if value is not None:
            _check_inverse(obj, self.spec, value)
        previous = obj._data.get(self.spec.name)
        if previous is not None:
            _unlink_inverse(obj, self.spec, previous)
        obj._data[self.spec.name] = value
        if value is not None:
            _link_inverse(obj, self.spec, value)
        obj._model._touch(obj, previous, value)


class TermOne(Generic[V]):
    """Descriptor for a scalar link to a compiled vocabulary individual."""

    def __init__(self, spec: PropertySpec) -> None:
        self.spec = spec

    def __set_name__(self, owner: type, name: str) -> None:
        if name != self.spec.name:
            raise TypeError(
                f"attribute {name!r} does not match spec name {self.spec.name!r}"
            )

    @overload
    def __get__(self, obj: None, owner: type) -> TermOne[V]: ...
    @overload
    def __get__(self, obj: Entity, owner: type) -> V | None: ...

    def __get__(self, obj: Entity | None, owner: type) -> TermOne[V] | V | None:
        if obj is None:
            return self
        return obj._data.get(self.spec.name)

    def __set__(self, obj: Entity, value: V | None) -> None:
        from .terms import TermValue

        obj._model._assert_mutable()
        _check_scalar(obj, self.spec, value)
        if value is not None and not isinstance(value, TermValue):
            raise RangeError(
                f"{type(obj).__name__}.{self.spec.name} expects a compiled "
                f"vocabulary term, got {type(value).__name__} ({value!r})"
            )
        if value is not None and self.spec.range_groups:
            obj._check_range(self.spec, value)
        if (
            value is not None
            and self.spec.term_ranges
            and not any(
                value.is_instance_of(class_iri) for class_iri in self.spec.term_ranges
            )
        ):
            allowed = " | ".join(self.spec.term_ranges)
            raise RangeError(
                f"{type(obj).__name__}.{self.spec.name} expects an instance "
                f"of {allowed}, got {value!r}"
            )
        obj._data[self.spec.name] = value
        obj._model._touch(obj)


class ValueOne(Generic[V]):
    """Descriptor for one unconstrained RDF value.

    S223 ``hasValue`` deliberately permits a simple literal as well as a
    named RDF resource.
    """

    def __init__(self, spec: PropertySpec) -> None:
        self.spec = spec

    def __set_name__(self, owner: type, name: str) -> None:
        if name != self.spec.name:
            raise TypeError(
                f"attribute {name!r} does not match spec name {self.spec.name!r}"
            )

    @overload
    def __get__(self, obj: None, owner: type) -> ValueOne[V]: ...
    @overload
    def __get__(self, obj: Entity, owner: type) -> V | None: ...

    def __get__(self, obj: Entity | None, owner: type) -> ValueOne[V] | V | None:
        if obj is None:
            return self
        from rdflib import Literal

        value = obj._data.get(self.spec.name)
        return value.toPython() if isinstance(value, Literal) else value

    def __set__(self, obj: Entity, value: V | None) -> None:
        obj._model._assert_mutable()
        _check_scalar(obj, self.spec, value)
        obj._data[self.spec.name] = value
        obj._model._touch(obj)


class EnumOne(Generic[V]):
    """Descriptor for a scalar enum property (``maxCount 1``).

    Values are :class:`~plumb.core.enums.EnumValue` constants; the range
    check walks the enumeration hierarchy (a ``Water_ChilledWater`` is
    accepted wherever a ``Substance_Medium`` is required).
    """

    def __init__(self, spec: PropertySpec) -> None:
        self.spec = spec

    def __set_name__(self, owner: type, name: str) -> None:
        if name != self.spec.name:  # pragma: no cover - generator invariant
            raise TypeError(
                f"attribute {name!r} does not match spec name {self.spec.name!r}"
            )

    @overload
    def __get__(self, obj: None, owner: type) -> EnumOne[V]: ...
    @overload
    def __get__(self, obj: Entity, owner: type) -> V | None: ...

    def __get__(self, obj: Entity | None, owner: type) -> EnumOne[V] | V | None:
        if obj is None:
            return self
        return obj._data.get(self.spec.name)

    def __set__(self, obj: Entity, value: V | None) -> None:
        obj._model._assert_mutable()
        _check_scalar(obj, self.spec, value)
        if value is not None:
            _check_enum(obj, self.spec, value)
        obj._data[self.spec.name] = value
        obj._model._touch(obj)


class EnumValues(Generic[V]):
    """Live, ordered, duplicate-free enum values of one entity property.

    Obtained by reading an :class:`EnumSet` attribute (``duct.has_role``).
    Like :class:`RelSet`, mutations are range-checked and write through to
    the model; it compares equal to a list of the same values.
    """

    __slots__ = ("_owner", "_spec")

    def __init__(self, owner: Entity, spec: PropertySpec) -> None:
        self._owner = owner
        self._spec = spec

    def _current(self) -> list[V]:
        return self._owner._data.get(self._spec.name, [])

    def _replace(self, values: list[V]) -> None:
        owner = self._owner
        owner._model._assert_mutable()
        values = list(dict.fromkeys(values))
        for value in values:
            _check_enum(owner, self._spec, value)
        _check_maximum(owner, self._spec, len(values))
        if owner._shape_constraints:
            from .shape_constraints import check_values

            check_values(owner, self._spec.name, values)
        owner._data[self._spec.name] = values
        owner._model._touch(owner)

    def add(self, *items: V) -> None:
        """Add one or more enum values. Duplicates are ignored."""
        self._owner._model._assert_mutable()
        values = list(self._current())
        for item in items:
            _check_enum(self._owner, self._spec, item)
            if item not in values:
                values.append(item)
        if len(values) != len(self._current()):
            self._replace(values)

    def remove(self, item: V) -> None:
        """Remove an enum value; raises ValueError if it is absent."""
        self._owner._model._assert_mutable()
        values = list(self._current())
        values.remove(item)
        self._replace(values)

    def clear(self) -> None:
        """Remove every value."""
        self._owner._model._assert_mutable()
        if self._current():
            self._replace([])

    def __iter__(self) -> Iterator[V]:
        return iter(list(self._current()))

    def __len__(self) -> int:
        return len(self._current())

    def __contains__(self, item: object) -> bool:
        return item in self._current()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EnumValues):
            return self._current() == other._current()
        if isinstance(other, (list, tuple)):
            return self._current() == list(other)
        return NotImplemented

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"EnumValues({self._spec.name}={self._current()!r})"


class EnumSet(Generic[V]):
    """Descriptor for a multi-valued enum property (e.g. 223 ``hasRole``).

    Reads as a live :class:`EnumValues` collection; assignment replaces
    contents.
    """

    def __init__(self, spec: PropertySpec) -> None:
        self.spec = spec

    def __set_name__(self, owner: type, name: str) -> None:
        if name != self.spec.name:  # pragma: no cover - generator invariant
            raise TypeError(
                f"attribute {name!r} does not match spec name {self.spec.name!r}"
            )

    @overload
    def __get__(self, obj: None, owner: type) -> EnumSet[V]: ...
    @overload
    def __get__(self, obj: Entity, owner: type) -> EnumValues[V]: ...

    def __get__(self, obj: Entity | None, owner: type) -> EnumSet[V] | EnumValues[V]:
        if obj is None:
            return self
        return EnumValues(obj, self.spec)

    def __set__(self, obj: Entity, value: Iterable[V]) -> None:
        EnumValues(obj, self.spec)._replace(_collection(obj, self.spec, value))


def _collection(obj: Entity, spec: PropertySpec, value: object) -> list:
    """The items of a multi-valued assignment; a lone value is an error.

    Enum constants support ``[...]`` hierarchy lookup, so iterating one by
    accident fails with a baffling KeyError rather than a TypeError.
    """
    from .entity import Entity
    from .enums import EnumValue

    if isinstance(value, (str, bytes, Entity, EnumValue, type)) or not isinstance(
        value, Iterable
    ):
        shown = value.__name__ if isinstance(value, type) else repr(value)
        raise RangeError(
            f"{type(obj).__name__}.{spec.name} takes a collection of values; "
            f"pass [{shown}]"
        )
    return list(value)


def _check_enum(obj: Entity, spec: PropertySpec, value: object) -> None:
    """Runtime enum-range check: value must live under an allowed root."""
    from .enums import EnumValue, _local

    if not isinstance(value, EnumValue):
        raise RangeError(
            f"{type(obj).__name__}.{spec.name} expects an enum constant "
            f"(from the generated enums module), got {type(value).__name__} "
            f"({value!r})"
        )
    groups = spec.range_groups or ((spec.enum_ranges,) if spec.enum_ranges else ())
    if not groups:
        return
    registry = obj.meta.registry
    if all(
        any(
            (root := registry.enums_by_iri.get(iri)) is not None and value.is_a(root)
            for iri in group
        )
        for group in groups
    ):
        return
    allowed = " & ".join(
        "(" + " | ".join(_local(iri) for iri in group) + ")" for group in groups
    )
    raise RangeError(
        f"{type(obj).__name__}.{spec.name} expects {allowed} (or a "
        f"descendant), got {_local(value.iri)}"
    )


def _check_scalar(obj: Entity, spec: PropertySpec, value: object) -> None:
    _check_maximum(obj, spec, int(value is not None))
    if obj._shape_constraints:
        from .shape_constraints import check_values

        check_values(obj, spec.name, value)


def _check_maximum(obj: Entity, spec: PropertySpec, count: int) -> None:
    if spec.max_count is not None and count > spec.max_count:
        raise RangeError(
            f"{type(obj).__name__}.{spec.name} permits at most {spec.max_count} values"
        )


class Lit(Generic[V]):
    """Descriptor for a scalar datatype property (a Python literal)."""

    def __init__(self, spec: PropertySpec) -> None:
        self.spec = spec

    def __set_name__(self, owner: type, name: str) -> None:
        if name != self.spec.name:  # pragma: no cover - generator invariant
            raise TypeError(
                f"attribute {name!r} does not match spec name {self.spec.name!r}"
            )

    @overload
    def __get__(self, obj: None, owner: type) -> Lit[V]: ...
    @overload
    def __get__(self, obj: Entity, owner: type) -> V | None: ...

    def __get__(self, obj: Entity | None, owner: type) -> Lit[V] | V | None:
        if obj is None:
            return self
        return obj._data.get(self.spec.name)

    def __set__(self, obj: Entity, value: V | None) -> None:
        obj._model._assert_mutable()
        _check_scalar(obj, self.spec, value)
        if value is not None and not _literal_ok(self.spec.datatype, value):
            raise RangeError(
                f"{type(obj).__name__}.{self.spec.name} expects "
                f"{self.spec.datatype.__name__ if self.spec.datatype else 'a literal'}, "
                f"got {type(value).__name__} ({value!r})"
            )
        obj._data[self.spec.name] = value
        obj._model._touch(obj)


def _literal_ok(datatype: type | None, value: object) -> bool:
    """Check a literal value against the spec's Python datatype.

    ``int`` is accepted where ``float`` is expected (but ``bool`` is not a
    number here, despite being an ``int`` subclass in Python).
    """
    if datatype is None:
        return True
    if datatype is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if datatype is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, datatype)


def _link_value(spec: PropertySpec, value: Any) -> Any:
    """Store a declared point as its port, or as its concrete point."""
    if spec.deferred:
        from .points import PointRef

        if isinstance(value, PointRef):
            return value._port
    return value


def _check_inverse(owner: Entity, spec: PropertySpec, target: object) -> None:
    """Validate an inverse edge without mutating the target."""
    from .entity import Entity

    if spec.inverse is None or not isinstance(target, Entity):
        return
    desc = getattr(type(target), spec.inverse, None)
    if not isinstance(desc, (Rel, RelOne)):
        return
    target._check_range(desc.spec, owner)
    if isinstance(desc, Rel):
        values = list(target._store_for(desc.spec))
        if owner not in values:
            values.append(owner)
    else:
        current = target._data.get(desc.spec.name)
        if current is not None and current is not owner:
            from .errors import ModelingError

            raise ModelingError(
                f"{target!r}.{desc.spec.name} is already {current!r}; "
                f"linking {owner!r}.{spec.name} would conflict "
                f"(remove the existing link first)"
            )
        values = [owner]
    _check_maximum(target, desc.spec, len(values))
    if target._shape_constraints:
        from .shape_constraints import check_values

        check_values(target, desc.spec.name, values if isinstance(desc, Rel) else owner)


def _link_inverse(owner: Entity, spec: PropertySpec, target: object) -> None:
    """Write a preflighted inverse edge without recursively invoking descriptors."""
    from .entity import Entity

    if spec.inverse is None or not isinstance(target, Entity):
        return
    desc = getattr(type(target), spec.inverse, None)
    if isinstance(desc, Rel):
        store = target._store_for(desc.spec)
        if owner not in store._items:
            store._items.append(owner)
    elif isinstance(desc, RelOne):
        target._data[desc.spec.name] = owner


def _unlink_inverse(owner: Entity, spec: PropertySpec, target: object) -> None:
    """Remove the mirrored inverse edge, if present."""
    if spec.inverse is None:
        return
    from .entity import Entity

    if not isinstance(target, Entity):
        return
    desc = getattr(type(target), spec.inverse, None)
    if isinstance(desc, Rel):
        store = target._store_for(desc.spec)
        if owner in store._items:
            store._items.remove(owner)
    elif isinstance(desc, RelOne):
        if target._data.get(desc.spec.name) is owner:
            target._data[desc.spec.name] = None
