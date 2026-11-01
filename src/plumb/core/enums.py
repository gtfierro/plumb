"""Enumeration constants generated from punned ontology hierarchies.

223P models enumerations (media, roles, aspects, ...) as a class hierarchy
under ``s223:EnumerationKind`` where every member is simultaneously a class
and an individual. In Python they become :class:`EnumValue` constants — not
Entity subclasses — because users *reference* them, never instantiate them:

    from plumb.s223 import enums
    Fluid_Air = enums.values.Fluid_Air
    Water_ChilledWater = enums.values.Water_ChilledWater
    Water_ChilledWater.is_a(Fluid_Water)   # hierarchy-aware -> True

The generated ``enums`` module exposes the top branches of the hierarchy,
and ``enums.values`` holds flat names (``Fluid-Air`` -> ``Fluid_Air``). Each
value also exposes its children as attributes for interactive exploration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from .meta import Registry


class EnumValue:
    """One enumeration member (a punned class/individual in the ontology)."""

    __slots__ = (
        "iri",
        "label",
        "definition",
        "parent",
        "parents",
        "constituents",
        "_children",
        "_registry",
    )

    def __init__(
        self,
        iri: str,
        *,
        label: str | None = None,
        definition: str | None = None,
        parent: EnumValue | None = None,
        _register_parent: bool = True,
    ) -> None:
        self.iri = iri
        self.label = label
        self.definition = definition
        self.parent = parent
        self.parents: tuple[EnumValue, ...] = (parent,) if parent is not None else ()
        # Constituents of a mixture medium (``s223:composedOf/ofConstituent``).
        self.constituents: tuple[EnumValue, ...] = ()
        self._children: dict[str, EnumValue] = {}
        self._registry: Registry | None = None
        if parent is not None and _register_parent:
            parent._children[_segment(iri)] = self

    @property
    def ontology_iri(self) -> str | None:
        """The defining vocabulary, retained when this value crosses packages."""
        return self._registry.ontology.iri if self._registry is not None else None

    def _add_parent(self, parent: EnumValue, *, register_child: bool = True) -> None:
        """Register an additional ontology superclass after module creation."""
        # Extensions can add ancestry without adding their values to the
        # dependency's shared child index (register_child=False).
        if parent not in self.parents:
            self.parents += (parent,)
            if register_child:
                parent._children[_segment(self.iri)] = self

    def is_a(self, other: EnumValue | str) -> bool:
        """True if this value is ``other`` or a descendant of it."""
        iri = other if isinstance(other, str) else other.iri
        frontier: list[EnumValue] = [self]
        seen: set[str] = set()
        while frontier:
            node = frontier.pop()
            if node.iri == iri:
                return True
            if node.iri in seen:
                continue
            seen.add(node.iri)
            frontier.extend(node.parents)
        return False

    def compatible_with(self, other: EnumValue) -> bool:
        """True if S223 deems the two media compatible.

        Pure media are compatible when one is the other or its descendant. A
        mixture is compatible with a pure medium when one of its constituents
        is, and with another mixture when they share a constituent. These are
        the cases of 223P's "Incompatible Medium" constraints, which compare
        an entity's ``hasMedium`` with the ``ofMedium`` of its properties.
        """

        def related(left: EnumValue, right: EnumValue) -> bool:
            return left.is_a(right) or right.is_a(left)

        if not self.constituents and not other.constituents:
            return related(self, other)
        if not self.constituents:
            return any(related(self, part) for part in other.constituents)
        if not other.constituents:
            return any(related(part, other) for part in self.constituents)
        return any(
            related(left, right)
            for left in self.constituents
            for right in other.constituents
        )

    @property
    def children(self) -> tuple[EnumValue, ...]:
        """Direct enum children, sorted by ontology-local name."""
        return tuple(
            sorted(
                self._children.values(),
                key=lambda item: (_local(item.iri), item.iri),
            )
        )

    @property
    def descendants(self) -> tuple[EnumValue, ...]:
        """All values below this one, in depth-first hierarchy order."""
        values: list[EnumValue] = []
        seen: set[str] = set()

        def walk(node: EnumValue) -> None:
            for child in node.children:
                if child.iri in seen:
                    continue
                seen.add(child.iri)
                values.append(child)
                walk(child)

        walk(self)
        return tuple(values)

    def __getitem__(self, name_or_iri: str) -> EnumValue:
        """Find a descendant by short name, flat name, or ontology IRI.

        For example, ``Fluid_Water["ChilledWater"]`` and
        ``Substance_Medium["Water_ChilledWater"]`` both select the same value.
        Ambiguous short names raise ``KeyError``; use a full name or IRI.
        """
        direct = self._children.get(name_or_iri)
        if direct is not None:
            return direct
        matches = [
            item
            for item in self.descendants
            if name_or_iri
            in (item.iri, _local(item.iri), _symbol(item.iri), _segment(item.iri))
        ]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise KeyError(
                f"{name_or_iri!r} is ambiguous below {_local(self.iri)}; "
                f"use one of {[item.iri for item in matches]}"
            )
        raise KeyError(f"{name_or_iri!r} is not below {_local(self.iri)}")

    def tree_text(
        self,
        *,
        max_depth: int | None = None,
        show_iris: bool = False,
    ) -> str:
        """Return a deterministic text tree rooted at this value.

        ``max_depth=0`` shows only this value (and an ellipsis when it has
        children); the default walks every descendant. Set ``show_iris`` to
        display full RDF identifiers instead of ontology-local names.
        """
        if max_depth is not None and (isinstance(max_depth, bool) or max_depth < 0):
            raise ValueError("max_depth must be a non-negative integer or None")

        def display(node: EnumValue) -> str:
            return node.iri if show_iris else _local(node.iri)

        lines = [display(self)]

        def walk(node: EnumValue, prefix: str, depth: int) -> None:
            children = node.children
            if max_depth is not None and depth >= max_depth:
                if children:
                    lines.append(f"{prefix}└── …")
                return
            for index, child in enumerate(children):
                last = index == len(children) - 1
                branch = "└── " if last else "├── "
                lines.append(f"{prefix}{branch}{display(child)}")
                walk(child, prefix + ("    " if last else "│   "), depth + 1)

        walk(self, "", 0)
        return "\n".join(lines)

    def tree(
        self,
        *,
        max_depth: int | None = None,
        show_iris: bool = False,
        file: TextIO | None = None,
    ) -> None:
        """Print the hierarchy rooted at this value."""
        print(
            self.tree_text(max_depth=max_depth, show_iris=show_iris),
            file=file,
        )

    def __getattr__(self, name: str) -> EnumValue:
        try:
            return self._children[name]
        except KeyError:
            raise AttributeError(
                f"{self!r} has no member {name!r} "
                f"(children: {sorted(self._children) or 'none'})"
            ) from None

    def __dir__(self) -> list[str]:
        """Show public metadata and direct children for interactive completion."""
        return sorted(
            {
                "iri",
                "ontology_iri",
                "label",
                "definition",
                "parent",
                "parents",
                "constituents",
                "children",
                "descendants",
                "is_a",
                "compatible_with",
                "tree",
                "tree_text",
                *self._children,
            }
        )

    def __repr__(self) -> str:
        return f"<enum {_local(self.iri)}>"


def _local(iri: str) -> str:
    for sep in ("#", "/"):
        if sep in iri:
            return iri.rsplit(sep, 1)[1]
    return iri


def _segment(iri: str) -> str:
    """Attribute name for hierarchical child access.

    223 locals repeat the parent as a prefix (``Fluid-Air``); the child
    segment is what follows the dash, sanitized to an identifier.
    """
    local = _local(iri)
    segment = local.split("-", 1)[1] if "-" in local else local
    return "".join(c if c.isalnum() or c == "_" else "_" for c in segment)


def _symbol(iri: str) -> str:
    """Flat Python-like name derived from an ontology-local enum name."""
    return "".join(c if c.isalnum() or c == "_" else "_" for c in _local(iri))
