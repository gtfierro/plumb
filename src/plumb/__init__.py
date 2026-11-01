"""plumb: author RDF building models as plain typed Python.

Generated ontology packages (``plumb.brick``, ...) provide the classes;
this top-level module re-exports the runtime pieces users touch directly.

    from plumb import Model
    from plumb.brick import AHU, VAV

    with Model("urn:ex/bldg1#") as m:
        ahu = AHU("ahu1")
        vav = VAV("vav1")
        ahu >> vav

    m.save("bldg1.ttl")
"""

from __future__ import annotations

from importlib.metadata import version as _version
from typing import TYPE_CHECKING, Literal, overload

if TYPE_CHECKING:
    from .s223 import Connectable as S223Connectable
    from .watr import Connectable as WaTrConnectable

from .core import (
    AmbiguousModelError,
    ConnectionHandle,
    Crossing,
    Hop,
    PortHandle,
    PortContract,
    PortSlot,
    PropertySchema,
    PropertySet,
    QuantityDefinition,
    quantity_field,
    ResolutionExplanation,
    Entity,
    EnumValue,
    Model,
    ModelingError,
    PlumbError,
    ResolutionError,
    ResolutionReport,
    ResolvedModel,
    TermValue,
    UnsatisfiableModelError,
    ValidationError,
    ValidationReport,
    current_model,
    exact,
)
from .core.points import PointGroupRef, PointRef, endpoint_owner
from .flowsheet import Flowsheet, flowsheet

__version__ = _version("plumb-rdf")


@overload
def connect(
    a: S223Connectable | WaTrConnectable | PortHandle | PointRef | PointGroupRef,
    b: Entity | PortHandle | PointRef | PointGroupRef,
    *,
    medium: EnumValue | None = None,
    connection: type[Entity] | None = None,
    name: str | None = None,
    ports: Literal["match", "new"] = "match",
) -> ConnectionHandle: ...


@overload
def connect(
    a: Entity,
    b: Entity | PortHandle | PointRef | PointGroupRef,
    *,
    medium: EnumValue | None = None,
    connection: type[Entity] | None = None,
    name: str | None = None,
    ports: Literal["match", "new"] = "match",
) -> ConnectionHandle | None: ...


def connect(
    a: Entity | PortHandle | PointRef | PointGroupRef,
    b: Entity | PortHandle | PointRef | PointGroupRef,
    *,
    medium: EnumValue | None = None,
    connection: type[Entity] | None = None,
    name: str | None = None,
    ports: Literal["match", "new"] = "match",
) -> ConnectionHandle | None:
    """Connect ``a`` to ``b`` along the flow direction; the functional form
    of ``a >> b`` for when you need to retain the connection intention.

    For S223/WaTr packages this returns a stable ``ConnectionHandle``.
    Named and unnamed connections select ports by the same rules. Use
    ``ports="new"`` to allocate fresh directed ports on bare equipment, or
    pass explicit point references. Port identity is independent of the name.
    ``medium=`` gives the Z3 resolver a flow-media hint, and the handle's
    ``medium`` property may be refined later. ``connection=`` constrains the
    materialized Connection subclass. Retrieve the concrete entity with
    ``resolved.connection(handle)`` after ``Model.resolve()``. Generated
    multi-valued properties can be staged with collection syntax, for example
    ``handle.has_role.add(role)``.
    For Brick-style packages it adds the flow property edge (``feeds``) and
    returns None (there is no intermediate resource to return).
    """
    if name == "":
        raise ValueError("connection name must not be empty")
    if ports not in {"match", "new"}:
        raise ValueError("ports must be 'match' or 'new'")
    connector = endpoint_owner(a)._CONNECTOR
    if connector is not None:
        return connector.connect(
            a, b, medium=medium, connection=connection, name=name, ports=ports
        )
    if isinstance(a, Entity) and a._RSHIFT is not None:
        getattr(a, a._RSHIFT).add(b)
        return None
    raise TypeError(f"{type(a).__name__} does not participate in flow connections")


__all__ = [
    "AmbiguousModelError",
    "ConnectionHandle",
    "Crossing",
    "Hop",
    "PortHandle",
    "PortContract",
    "PortSlot",
    "PropertySchema",
    "PropertySet",
    "QuantityDefinition",
    "quantity_field",
    "PointGroupRef",
    "PointRef",
    "ResolutionExplanation",
    "Entity",
    "EnumValue",
    "Flowsheet",
    "Model",
    "ModelingError",
    "PlumbError",
    "ResolutionError",
    "ResolutionReport",
    "ResolvedModel",
    "TermValue",
    "UnsatisfiableModelError",
    "ValidationReport",
    "ValidationError",
    "connect",
    "current_model",
    "exact",
    "flowsheet",
    "__version__",
]
