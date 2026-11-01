"""Naming policy: ontology terms -> Python identifiers.

Deterministic and documented, because generated names are user-facing API:

- classes keep their IRI local name, sanitized to a valid identifier
  (Brick's ``Air_Handling_Unit`` style survives unchanged);
- properties are the local name converted camelCase -> snake_case
  (``hasPoint`` -> ``has_point``);
- names colliding with reserved Entity API (``name``, ``type``, ``label``,
  ``comment``, ``meta``, ``model``, ``contains``, ``ports``,
  ``describe_ports``, the find and walk methods, ...) or Python keywords
  get a trailing ``_``;
- two terms mapping to the same Python name are disambiguated by suffixing
  ``_2``, ``_3``, ... (stable across runs); deprecated terms are suffixed
  before current ones, then sorted-IRI order decides.
"""

from __future__ import annotations

import keyword
import re
from collections.abc import Set

#: Attribute/method names owned by the Entity base class.
RESERVED = frozenset(
    {
        "name",
        "type",
        "label",
        "comment",
        "meta",
        "model",
        "contains",
        "ports",
        "describe_ports",
        "apply_properties",
        "quantity",
        "boundary",
        "port",
        "contents",
        "descendants",
        "container",
        "containers",
        "find",
        "find_all",
        "find_parent",
        "find_parents",
        "walk",
        "find_next",
        "find_all_next",
        "find_previous",
        "find_all_previous",
    }
) | frozenset(keyword.kwlist)

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_INVALID = re.compile(r"[^0-9A-Za-z_]")
MODULE_RESERVED = frozenset({"ONTOLOGY", "REGISTRY"})

# Python-facing names for the S223 point properties most commonly used by
# equipment authors. Keep this mapping IRI-scoped so unrelated ontologies
# such as Brick retain their established property names.
_S223_POINT_NAMES = {
    "http://data.ashrae.org/standard223#hasMedium": "medium",
    "http://data.ashrae.org/standard223#isConnectionPointOf": "owner",
    "http://data.ashrae.org/standard223#connectsThrough": "connection",
    "http://data.ashrae.org/standard223#pairedConnectionPoint": "paired_with",
}


def local_name(iri: str) -> str:
    """The fragment/last path segment of an IRI."""
    for sep in ("#", "/"):
        if sep in iri:
            candidate = iri.rsplit(sep, 1)[1]
            if candidate:
                return candidate
    return iri


def class_name(iri: str) -> str:
    """Python class name for an ontology class IRI."""
    name = _sanitize(local_name(iri))
    return name + "_" if name in MODULE_RESERVED else name


def property_name(iri: str) -> str:
    """Python attribute name for an ontology property IRI."""
    if iri in _S223_POINT_NAMES:
        return _S223_POINT_NAMES[iri]
    snake = _CAMEL_BOUNDARY.sub("_", local_name(iri)).lower()
    return _sanitize(snake)


def _sanitize(name: str) -> str:
    """Make a valid, non-reserved Python identifier."""
    name = _INVALID.sub("_", name)
    if name[:1].isdigit():
        name = "_" + name
    if name in RESERVED:
        name += "_"
    return name


def disambiguate(
    assignments: dict[str, str],
    *,
    preferred_namespace: str | None = None,
    deprecated: Set[str] = frozenset(),
) -> dict[str, str]:
    """Resolve name collisions across a set of IRIs.

    ``assignments`` maps IRI -> desired Python name. Returns IRI -> final
    name, where every duplicate group keeps the name for its first IRI and
    suffixes ``_2``, ``_3``, ... onto the rest. Current terms precede
    ``deprecated`` ones, then ``preferred_namespace`` terms, then sorted IRI
    order: a deprecated ``brick:Building`` yields ``Building`` to its
    replacement ``rec:Building``.
    """
    by_name: dict[str, list[str]] = {}
    for iri in sorted(assignments):
        by_name.setdefault(assignments[iri], []).append(iri)
    final: dict[str, str] = {}
    # Reserve natural names before allocating suffixes. If the ontology already
    # contains Foo_2, a collision on Foo must skip that spelling rather than
    # steal it and force an unrelated term to acquire a new public name.
    reserved = set(assignments.values())
    used: set[str] = set()
    for name, iris in by_name.items():
        ordered = sorted(
            iris,
            key=lambda iri: (
                iri in deprecated,
                not (
                    preferred_namespace is not None
                    and iri.startswith(preferred_namespace)
                ),
                iri,
            ),
        )
        for index, iri in enumerate(ordered):
            candidate = name
            suffix = index + 1
            while candidate in used or (candidate != name and candidate in reserved):
                suffix = max(2, suffix)
                candidate = f"{name}_{suffix}"
                suffix += 1
            final[iri] = candidate
            used.add(candidate)
    return final
