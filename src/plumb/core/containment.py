"""Containment: `with` nesting and ``contains()``.

Users express *what contains what*; the predicate is negotiated from the
(container class, child class) pair using a table registered by the generated
package (e.g. Brick: Location x Equipment -> the equipment's ``has_location``).

Two entry points, one mechanism:

- entering an entity's ``with`` block pushes it onto an ambient stack; every
  entity constructed inside attaches to the innermost *compatible* container;
- ``container.contains(child)`` applies the same negotiation explicitly.

Rules distinguish which side owns the edge: ``hasPart`` is asserted from the
container, ``hasLocation`` from the child. Either way the user-facing
direction is "container contains child".
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator, Literal

from .errors import ContainmentError
from .relations import Rel, RelOne

if TYPE_CHECKING:
    from .entity import Entity
    from .meta import Registry

#: Ambient stack of entities whose ``with`` blocks are currently open.
_stack: ContextVar[tuple[Entity, ...]] = ContextVar(
    "plumb_containment_stack", default=()
)

#: When set, freshly created entities skip ambient attachment. Used by
#: machinery (connection negotiation) that creates helper entities the user
#: never asked to contain anywhere.
_suppressed: ContextVar[bool] = ContextVar(
    "plumb_containment_suppressed", default=False
)


@contextmanager
def suppressed() -> Iterator[None]:
    """Create entities without attaching them to open ``with`` scopes."""
    token = _suppressed.set(True)
    try:
        yield
    finally:
        _suppressed.reset(token)


@dataclass(frozen=True)
class ContainmentRule:
    """One row of the negotiation table.

    ``container``/``child`` are Python class names (resolved through the
    package registry so rules can be declared before classes exist).
    ``edge_from`` says which side the property lives on.
    """

    container: str
    child: str
    prop: str
    edge_from: Literal["container", "child"] = "container"


class ContainmentTable:
    """Per-package containment negotiation table."""

    def __init__(self, registry: Registry) -> None:
        self._registry = registry
        self.rules: list[ContainmentRule] = []

    def register(
        self,
        container: str,
        child: str,
        prop: str,
        *,
        edge_from: Literal["container", "child"] = "container",
    ) -> None:
        """Add a rule. Called from generated package setup code."""
        rule = ContainmentRule(container, child, prop, edge_from)
        if rule not in self.rules:
            self.rules.append(rule)

    def find(self, container: Entity, child: Entity) -> ContainmentRule | None:
        """Match a rule for this pair, or None.

        Multiple matches raise :class:`ContainmentError` — the user should
        say which property they meant via ``contains(child, via=...)``.
        """
        matches = [
            rule
            for rule in self.rules
            if container.meta.is_a(self._registry.resolve(rule.container))
            and child.meta.is_a(self._registry.resolve(rule.child))
        ]
        if not matches:
            return None
        if len(matches) > 1:
            options = ", ".join(repr(r.prop) for r in matches)
            raise ContainmentError(
                f"{type(container).__name__} can contain "
                f"{type(child).__name__} via more than one property "
                f"({options}); disambiguate with "
                f"{_name(container)}.contains({_name(child)}, via=...)"
            )
        return matches[0]

    def apply(
        self, container: Entity, child: Entity, *, via: str | None = None
    ) -> None:
        """Create the containment edge between two entities."""
        if via is not None:
            _apply_via(container, child, via)
            return
        rule = self.find(container, child)
        if rule is None:
            raise ContainmentError(
                f"no containment rule relates {type(container).__name__} "
                f"(container) and {type(child).__name__} (child); use "
                f"{_name(container)}.contains({_name(child)}, via='<property>') "
                f"to pick a property explicitly"
            )
        if rule.edge_from == "container":
            _add_edge(container, rule.prop, child)
        else:
            _add_edge(child, rule.prop, container)


def push(entity: Entity) -> None:
    """Enter an entity's containment scope (``with entity:``)."""
    _stack.set(_stack.get() + (entity,))


def pop(entity: Entity) -> None:
    """Leave an entity's containment scope."""
    stack = _stack.get()
    if not stack or stack[-1] is not entity:  # pragma: no cover - misuse guard
        raise ContainmentError("mismatched containment scope exit")
    _stack.set(stack[:-1])


def attach(child: Entity) -> None:
    """Attach a freshly constructed entity to the ambient containment stack.

    Walks the stack innermost-first and applies the first matching rule.
    If containers are open but none is compatible, that's almost certainly a
    modeling mistake, so we raise rather than silently produce a floating
    entity — construct outside the ``with`` block to opt out.
    """
    stack = _stack.get()
    if not stack or _suppressed.get():
        return
    table = child.meta.registry.containment
    tried: list[str] = []
    for container in reversed(stack):
        if container is child:
            continue
        rule = table.find(container, child)
        if rule is not None:
            table.apply(container, child)
            return
        tried.append(type(container).__name__)
    raise ContainmentError(
        f"{type(child).__name__} was created inside "
        f"`with` block(s) of {', '.join(tried)}, but no containment rule "
        f"accepts it there; create it outside the block or attach it "
        f"explicitly with contains(..., via=...)"
    )


def _apply_via(container: Entity, child: Entity, via: str) -> None:
    """Explicit-property escape hatch: find `via` on either side."""
    for subject, obj in ((container, child), (child, container)):
        desc = getattr(type(subject), via, None)
        if isinstance(desc, (Rel, RelOne)):
            _add_edge(subject, via, obj)
            return
    raise ContainmentError(
        f"neither {type(container).__name__} nor {type(child).__name__} "
        f"has a property named {via!r}"
    )


def _add_edge(subject: Entity, prop: str, obj: Entity) -> None:
    """Write one edge through the subject's descriptor (range-checked)."""
    desc = getattr(type(subject), prop)
    if isinstance(desc, RelOne):
        setattr(subject, prop, obj)
    else:
        getattr(subject, prop).add(obj)


def _name(entity: Entity) -> str:
    """Best-effort variable-ish name for error message snippets."""
    return entity.name if entity.name.isidentifier() else repr(entity.name)
