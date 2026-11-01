"""The Entity base class and the ``.meta`` metadata accessor.

Every generated ontology class subclasses :class:`Entity`. Instances are plain
Python objects; the RDF view (IRIs, triples) exists only in metadata and in
the model's serializer. User code should never need an import from ``rdflib``.
"""

from __future__ import annotations

import builtins
from collections.abc import Callable, Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Iterator,
    Literal,
    Self,
    TypeVar,
    overload,
)

from . import containment as _containment
from .errors import ModelingError, RangeError
from .meta import (
    CPConstraint,
    ClassInfo,
    OntologyInfo,
    PortContract,
    PortSlot,
    PropertySpec,
    Registry,
    _port_requirements,
)
from .relations import (
    EnumOne,
    EnumSet,
    Lit,
    Rel,
    RelOne,
    RelSet,
    TermOne,
    ValueOne,
)
from .terms import TermValue

if TYPE_CHECKING:
    from .enums import EnumValue
    from .model import Model
    from .property_schema import PropertySchema, PropertySet, QuantityAmount
    from .points import PointRef
    from .resolution import PortHandle
    from .model import EntityTypeFilter
    from .traversal import Crossing, Hop

_EntityT = TypeVar("_EntityT", bound="Entity")

#: The ``through=`` argument of the walk methods.
type Through = Mapping[str, object] | Callable[[Crossing], object] | None


class ClassMetaView:
    """Read-only view of a generated class's ontology provenance.

    Accessed as ``AHU.meta``. Everything here comes from the ontology at
    generation time; the generated docstrings render the same data.
    """

    __slots__ = ("_cls",)

    def __init__(self, cls: type[Entity]) -> None:
        self._cls = cls

    @property
    def iri(self) -> str:
        """IRI of the ontology class."""
        return self._cls._classinfo.iri

    @property
    def label(self) -> str | None:
        """``rdfs:label`` of the class."""
        return self._cls._classinfo.label

    @property
    def definition(self) -> str | None:
        """``skos:definition`` / ``rdfs:comment`` text."""
        return self._cls._classinfo.definition

    @property
    def ontology(self) -> OntologyInfo:
        """The ontology this class was generated from."""
        return self._cls._classinfo.ontology

    @property
    def registry(self) -> Registry:
        """The generated package's class registry."""
        return self._cls._classinfo.registry

    @property
    def canonical(self) -> type[Entity]:
        """The defining ontology class behind a package-specific typed view."""
        info = self._cls._classinfo
        return info.canonical or info.cls or self._cls

    @property
    def parents(self) -> tuple[type[Entity], ...]:
        """Direct ontology superclasses (as Python classes)."""
        iris = self._cls._classinfo.parent_iris
        if iris is not None:
            return tuple(
                self.registry.by_iri[iri] for iri in iris if iri in self.registry.by_iri
            )
        return tuple(
            base
            for base in self._cls.__bases__
            if issubclass(base, Entity) and "_classinfo" in base.__dict__
        )

    def is_a(self, parent: type[Entity] | str) -> bool:
        """Test ontology ancestry independently of Python inheritance repairs."""
        iri = parent if isinstance(parent, str) else parent.meta.iri
        return any(
            info.iri == iri or iri in info.ancestor_iris
            for base in self._cls.__mro__
            if (info := base.__dict__.get("_classinfo")) is not None
        )

    @property
    def subclasses(self) -> tuple[type[Entity], ...]:
        """Direct subclasses registered in this generated package."""
        return self.registry.subclasses(self._cls)

    @property
    def children(self) -> tuple[type[Entity], ...]:
        """Direct child classes; alias for :attr:`subclasses`."""
        return self.subclasses

    @property
    def descendants(self) -> tuple[type[Entity], ...]:
        """All registered subclasses at any depth, sorted by Python name."""
        return self.registry.subclasses(self._cls, recursive=True)

    def tree(self, *, max_depth: int | None = None) -> str:
        """Render this class and its registered subclass hierarchy as text."""
        return self.registry.tree(self._cls, max_depth=max_depth)

    def __getitem__(self, name_or_iri: str) -> type[Entity]:
        """Look up a descendant by Python name, short name, or class IRI.

        ``Process.meta["ReverseOsmosis"]`` accepts the short name of a
        generated ``Process_ReverseOsmosis`` class. Full Python names and IRIs
        also work. A class outside this subtree raises ``KeyError``.
        """
        registry = self.registry
        cls = registry.by_name.get(name_or_iri)
        if cls is None:
            cls = registry.by_name.get(f"{self._cls.__name__}_{name_or_iri}")
        if cls is None:
            cls = registry.by_iri.get(name_or_iri)
        if cls is None or cls is self._cls or not cls.meta.is_a(self._cls):
            raise KeyError(
                f"{name_or_iri!r} is not a registered subclass of {self._cls.__name__}"
            )
        return cls

    @property
    def properties(self) -> tuple[PropertySpec, ...]:
        """Effective property specs: inherited plus own, own winning."""
        return tuple(self._cls._effective_specs().values())

    @property
    def port_contract(self) -> PortContract:
        """Inherited SHACL requirements for connection points on this class.

        Slots describe unconditional count, direction, point class, and
        allowed medium roots. Boolean alternatives remain in ``constraints``.
        Named shape slots are included where compiled; inspect ``instance.ports``
        for the concrete and authored points on a particular instance.
        """
        registry = self.registry

        def medium(iri: str | None) -> EnumValue | str | None:
            if iri is None:
                return None
            return registry.enums_by_iri.get(iri, iri)

        slots: list[PortSlot] = []
        constraints: list[CPConstraint] = []
        raw_slots, raw_constraints = _port_requirements(self._cls)
        for slot in raw_slots:
            slots.append(
                PortSlot(
                    point_class=registry.resolve(slot.cp_class),
                    direction=slot.direction,
                    medium=medium(slot.medium),
                    medium_options=tuple(
                        registry.enums_by_iri.get(iri, iri)
                        for iri in slot.medium_options
                    ),
                    min_count=slot.min_count,
                    max_count=slot.max_count,
                    name=slot.name,
                    label=slot.label,
                )
            )
        constraints.extend(raw_constraints)
        return PortContract(tuple(slots), tuple(constraints))

    def describe_ports(self) -> str:
        """Render this class's inherited port requirements for authoring."""
        return (
            f"{self._cls.__name__} port requirements\n{self.port_contract.describe()}"
        )

    @property
    def abstract(self) -> bool:
        """True for organizational classes not meant to be instantiated."""
        return self._cls._classinfo.abstract

    def __repr__(self) -> str:
        return f"<meta of {self._cls.__name__}: {self.iri}>"


class InstanceMetaView(ClassMetaView):
    """Per-instance metadata: everything on the class view, plus identity."""

    __slots__ = ("_obj",)

    def __init__(self, obj: Entity) -> None:
        super().__init__(type(obj))
        self._obj = obj

    @property
    def cls(self) -> type[Entity]:
        """The generated class of this instance."""
        return self._cls

    @property
    def instance_iri(self) -> str:
        """The IRI minted for this instance by its model."""
        return self._obj._iri

    @property
    def model(self) -> Model:
        """The model this instance belongs to."""
        return self._obj._model

    def __repr__(self) -> str:
        return f"<meta of {self._obj!r}: {self.instance_iri}>"


class _MetaDescriptor:
    """Serves ``.meta`` on both classes and instances."""

    @overload
    def __get__(self, obj: None, owner: type[Entity]) -> ClassMetaView: ...
    @overload
    def __get__(self, obj: Entity, owner: type[Entity]) -> InstanceMetaView: ...

    def __get__(
        self, obj: Entity | None, owner: type[Entity]
    ) -> ClassMetaView | InstanceMetaView:
        if obj is None:
            return ClassMetaView(owner)
        return InstanceMetaView(obj)


class Entity:
    """Base class for all generated ontology classes.

    Construction requires an active :class:`~plumb.core.model.Model`
    (either ambient, via ``with Model(...)``, or passed as ``model=``).
    The first argument is the entity's local name; binding mints its IRI
    under the model's namespace. When omitted, a name is
    auto-generated per model as ``<class>_<n>`` (``vav_1``, ``vav_2``, ...).

    Reserved attribute names (``name``, ``type``, ``label``, ``comment``,
    ``meta``, ``model``, ``ports``, ``describe_ports``, the find and walk
    methods, ...; see ``plumb.gen.naming.RESERVED``): ontology properties
    that would collide are renamed by the generator's collision policy.
    """

    #: Ontology provenance; set in the class body by generated code.
    _classinfo: ClassVar[ClassInfo]

    #: Property name that ``>>`` sugar maps to (e.g. Brick sets "feeds" on
    #: Equipment); None disables the operator for the class.
    _RSHIFT: ClassVar[str | None] = None

    #: Connection negotiator hook (e.g. 223 sets one on Connectable). When
    #: set, ``>>`` delegates to ``_CONNECTOR.connect(a, b)`` instead of the
    #: simple ``_RSHIFT`` property. See plumb.connect223.
    _CONNECTOR: ClassVar[Any | None] = None

    meta = _MetaDescriptor()
    _point_declarations: ClassVar[dict[str, Any]] = {}
    _shape_constraints: ClassVar[tuple[Any, ...]] = ()
    _shape_max_ports: ClassVar[int | None] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        info = cls.__dict__.get("_classinfo")
        if info is not None:
            info.registry.register(cls)

    def __init__(
        self,
        name: str | None = None,
        *,
        label: str | None = None,
        comment: str | None = None,
        model: Model | None = None,
        **props: Any,
    ) -> None:
        if "_classinfo" not in _mro_dicts(type(self)):
            raise TypeError("Entity cannot be instantiated directly")
        if self._classinfo_effective().abstract:
            raise ModelingError(
                f"{type(self).__name__} is an organizational class and "
                f"cannot be instantiated; pick a concrete subclass"
            )
        from .model import current_model

        m = model if model is not None else current_model()
        if m is None:
            raise ModelingError(
                f"no active Model: create entities inside `with Model(...):` "
                f"or pass model= to {type(self).__name__}(...)"
            )
        # Binding comes before property assignment: inverse edges and generated
        # helpers need a real model/IRI. The transaction makes that early binding
        # safe when a later required-value or containment check rejects the
        # constructor. No ghost object or consumed automatic name may survive.
        with m._atomic():
            if name is None:
                name = m._auto_name(type(self))
            self._name = name
            self._label = label if label is not None else name
            self._comment = comment
            self._data: dict[str, Any] = {}
            self._rels: dict[str, RelSet[Any]] = {}
            self._iri: str = ""  # minted by Model._bind below
            self._model: Model = m
            m._bind(self)
            self._named_points: dict[str, Any] = {}
            if self._shape_constraints:
                from .shape_constraints import initial_values

                props = initial_values(self, props)
            for key, value in props.items():
                descriptor = getattr(type(self), key, None)
                if not isinstance(
                    descriptor,
                    (Rel, RelOne, TermOne, ValueOne, Lit, EnumOne, EnumSet),
                ):
                    raise ModelingError(
                        f"{type(self).__name__} has no property {key!r}"
                    )
                if value is None:
                    continue
                setattr(self, key, value)

            domain = self.meta.registry._domain
            if domain is not None and not m._resolving:
                domain.initialize(self)
            elif domain is None and type(self)._point_declarations:
                raise ModelingError("named points require a connection domain")

            self._apply_class_defaults()
            self._check_required()
            if not m._resolving:
                _containment.attach(self)
            if self._CONNECTOR is not None and not m._resolving:
                # e.g. 223: materialize connection points the class's shapes
                # require, so a fresh Fan already has its air inlet/outlet.
                self._CONNECTOR.on_create(self)

    # -- identity ---------------------------------------------------------

    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)

    @property
    def name(self) -> str:
        """Local name; combined with the model namespace to mint the IRI."""
        return self._name

    @property
    def type(self) -> str:
        """Python class name, such as ``"Duct"``.

        Use :attr:`meta.iri <ClassMetaView.iri>` for the ontology class IRI.
        """
        return type(self).__name__

    @property
    def label(self) -> str:
        """Human-readable label (``rdfs:label``); defaults to the name."""
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._model._assert_mutable()
        self._label = value
        self._model._touch(self)

    @property
    def comment(self) -> str | None:
        """Free-text note serialized as ``rdfs:comment``."""
        return self._comment

    @comment.setter
    def comment(self, value: str | None) -> None:
        self._model._assert_mutable()
        self._comment = value
        self._model._touch(self)

    # -- containment ------------------------------------------------------

    def contains(self, *children: Entity, via: str | None = None) -> Self:
        """Declare that this entity contains the given entities.

        The predicate is negotiated per (container, child) class pair from
        the package's containment table; pass ``via='<property>'`` to pick
        one explicitly. Returns ``self`` for chaining.
        """
        table = self.meta.registry.containment
        for child in children:
            table.apply(self, child, via=via)
        return self

    @property
    def contents(self) -> tuple[Entity, ...]:
        """Entities this one directly contains, in model order."""
        from .traversal import contents

        return contents(self)

    @property
    def descendants(self) -> Iterator[Entity]:
        """Everything this entity contains, depth-first, each entity once."""
        from .traversal import descendants

        return descendants(self)

    @property
    def container(self) -> Entity | None:
        """The direct container; raises ``ModelingError`` if there are several."""
        from .traversal import container

        return container(self)

    @property
    def containers(self) -> Iterator[Entity]:
        """Every container of this entity, nearest first."""
        from .traversal import containers

        return containers(self)

    def find_all(
        self,
        entity_type: EntityTypeFilter[_EntityT] = None,
        /,
        *,
        recursive: bool = True,
        limit: int | None = None,
        attrs: dict[str, object] | None = None,
        **attributes: object,
    ) -> list[_EntityT]:
        """Contained entities matching a type and filters, as ``Model.find_all``.

        Searches everything this entity contains, or only its direct
        contents with ``recursive=False``.
        """
        from .traversal import contents, descendants, merge_filters, select

        candidates = descendants(self) if recursive else contents(self)
        return select(candidates, entity_type, merge_filters(attributes, attrs), limit)

    def find(
        self,
        entity_type: EntityTypeFilter[_EntityT] = None,
        /,
        *,
        recursive: bool = True,
        attrs: dict[str, object] | None = None,
        **attributes: object,
    ) -> _EntityT | None:
        """The first contained entity matching a type and filters, or ``None``."""
        found = self.find_all(
            entity_type, recursive=recursive, limit=1, attrs=attrs, **attributes
        )
        return found[0] if found else None

    def find_parents(
        self,
        entity_type: EntityTypeFilter[_EntityT] = None,
        /,
        *,
        limit: int | None = None,
        attrs: dict[str, object] | None = None,
        **attributes: object,
    ) -> list[_EntityT]:
        """Containers matching a type and filters, nearest first."""
        from .traversal import containers, merge_filters, select

        filters = merge_filters(attributes, attrs)
        return select(containers(self), entity_type, filters, limit)

    def find_parent(
        self,
        entity_type: EntityTypeFilter[_EntityT] = None,
        /,
        *,
        attrs: dict[str, object] | None = None,
        **attributes: object,
    ) -> _EntityT | None:
        """The nearest container matching a type and filters, or ``None``."""
        found = self.find_parents(entity_type, limit=1, attrs=attrs, **attributes)
        return found[0] if found else None

    # -- topology ---------------------------------------------------------

    def walk(
        self,
        direction: Literal["downstream", "upstream"] = "downstream",
        *,
        through: Through = None,
        descend: bool = False,
        include_connections: bool = False,
        max_hops: int | None = None,
    ) -> Iterator[Hop]:
        """Walk the connection graph breadth-first, nearest entities first.

        ``through`` prunes the path: a mapping of filters checked against
        each pipe or connection crossed, or a callable given each
        :class:`~plumb.core.traversal.Crossing`. ``descend`` steps into
        containers through ``maps_to``. Pipes and connections are yielded
        only with ``include_connections``. See ``docs/traversal.md``.
        """
        from .traversal import walk

        return walk(
            self,
            direction,
            through=through,
            descend=descend,
            include_connections=include_connections,
            max_hops=max_hops,
        )

    def find_all_next(
        self,
        entity_type: EntityTypeFilter[_EntityT] = None,
        /,
        *,
        through: Through = None,
        descend: bool = False,
        include_connections: bool = False,
        max_hops: int | None = None,
        limit: int | None = None,
        attrs: dict[str, object] | None = None,
        **attributes: object,
    ) -> list[_EntityT]:
        """Downstream entities matching a type and filters, nearest first.

        Filters apply to the results; ``through`` applies to the path.
        """
        return self._find_along(
            "downstream",
            entity_type,
            attributes,
            attrs,
            limit=limit,
            through=through,
            descend=descend,
            include_connections=include_connections,
            max_hops=max_hops,
        )

    def find_next(
        self,
        entity_type: EntityTypeFilter[_EntityT] = None,
        /,
        *,
        through: Through = None,
        descend: bool = False,
        include_connections: bool = False,
        max_hops: int | None = None,
        attrs: dict[str, object] | None = None,
        **attributes: object,
    ) -> _EntityT | None:
        """The nearest downstream entity matching a type and filters."""
        found = self.find_all_next(
            entity_type,
            through=through,
            descend=descend,
            include_connections=include_connections,
            max_hops=max_hops,
            limit=1,
            attrs=attrs,
            **attributes,
        )
        return found[0] if found else None

    def find_all_previous(
        self,
        entity_type: EntityTypeFilter[_EntityT] = None,
        /,
        *,
        through: Through = None,
        descend: bool = False,
        include_connections: bool = False,
        max_hops: int | None = None,
        limit: int | None = None,
        attrs: dict[str, object] | None = None,
        **attributes: object,
    ) -> list[_EntityT]:
        """Upstream entities matching a type and filters, nearest first."""
        return self._find_along(
            "upstream",
            entity_type,
            attributes,
            attrs,
            limit=limit,
            through=through,
            descend=descend,
            include_connections=include_connections,
            max_hops=max_hops,
        )

    def find_previous(
        self,
        entity_type: EntityTypeFilter[_EntityT] = None,
        /,
        *,
        through: Through = None,
        descend: bool = False,
        include_connections: bool = False,
        max_hops: int | None = None,
        attrs: dict[str, object] | None = None,
        **attributes: object,
    ) -> _EntityT | None:
        """The nearest upstream entity matching a type and filters."""
        found = self.find_all_previous(
            entity_type,
            through=through,
            descend=descend,
            include_connections=include_connections,
            max_hops=max_hops,
            limit=1,
            attrs=attrs,
            **attributes,
        )
        return found[0] if found else None

    def _find_along(
        self,
        direction: Literal["downstream", "upstream"],
        entity_type: object,
        attributes: dict[str, object],
        attrs: dict[str, object] | None,
        *,
        limit: int | None,
        **options: Any,
    ) -> list[Any]:
        from .traversal import find_along, merge_filters

        filters = merge_filters(attributes, attrs)
        return find_along(self, direction, entity_type, filters, limit=limit, **options)

    def quantity(
        self,
        name: str,
        value: float | QuantityAmount,
        *,
        unit: TermValue | None = None,
        kind: TermValue,
        capability: Literal["static", "observable", "actuatable"] = "static",
        label: str | None = None,
        **properties: Any,
    ) -> Entity:
        """Create and attach a named S223 quantifiable property to this object.

        ``capability`` selects a static, observable, or actuatable property.
        Measurement aspects are independent; pass ``has_aspect`` explicitly.
        A ``QuantityAmount`` supplies its own unit.
        The returned property is an ordinary model entity.
        """
        if not hasattr(self, "has_property"):
            raise TypeError(f"{type(self).__name__} does not support has_property")
        from plumb.qudt import _attached_quantity

        return _attached_quantity(
            self,
            name,
            value,
            unit=unit,
            kind=kind,
            capability=capability,
            label=label,
            **properties,
        )

    def sensor(
        self,
        name: str,
        *,
        kind: TermValue | EnumValue,
        unit: TermValue | None = None,
        sensor_class: builtins.type[Entity] | None = None,
        value: float | QuantityAmount | EnumValue | None = None,
        label: str | None = None,
        **properties: Any,
    ) -> Entity:
        """Add a sensor that observes a quantity here.

        Creates an observable ``<name>-value`` property of ``kind`` on this
        location and a sensor named ``name`` observing it. The sensor class
        is the most specific one for ``kind`` (``TurbidityMeter`` for
        Turbidity) unless ``sensor_class`` is given; ``properties`` such as
        ``of_medium`` go to the observed property.
        """
        from plumb.qudt import _attached_sensor

        return _attached_sensor(
            self,
            name,
            kind=kind,
            unit=unit,
            sensor_class=sensor_class,
            value=value,
            label=label,
            **properties,
        )

    def actuator(
        self,
        name: str,
        *,
        kind: TermValue | EnumValue,
        unit: TermValue | None = None,
        value: float | QuantityAmount | EnumValue | None = None,
        label: str | None = None,
        **properties: Any,
    ) -> Entity:
        """Add an actuator that commands this equipment.

        Creates an actuatable ``<name>-command`` property and an ``Actuator``
        named ``name`` that ``actuates`` this equipment; both are
        ``actuated_by_property`` the command. ``kind`` is a QUDT quantity
        kind with ``unit=`` (a speed or position setpoint) or an enumeration
        kind such as ``Binary_OnOff`` (a start/stop command).
        """
        from plumb.qudt import _attached_actuator

        return _attached_actuator(
            self,
            name,
            kind=kind,
            unit=unit,
            value=value,
            label=label,
            **properties,
        )

    def apply_properties(
        self, schema: PropertySchema, *, prefix: str | None = None
    ) -> PropertySet:
        """Attach fresh properties from a generated RDF/SHACL value schema."""
        from .property_schema import apply_properties

        return apply_properties(self, schema, prefix=prefix)

    def boundary(self, *points: Entity | PortHandle | PointRef) -> Self:
        """Mark concrete or deferred connection points as system boundaries."""
        from .lifecycle import require_domain

        require_domain(self).boundary(self, points)
        return self

    def port(
        self,
        name: str,
        *,
        direction: str,
        medium: EnumValue | None = None,
        label: str | None = None,
    ) -> PortHandle:
        """Declare a named deferred connection point for solver negotiation."""
        from .lifecycle import require_domain

        return require_domain(self).port(
            self, name, direction=direction, medium=medium, label=label
        )

    @classmethod
    def describe_ports(cls) -> str:
        """Summarize the class's port directions and SHACL requirements.

        This describes what the ontology permits or requires, rather than
        the concrete and deferred points on a particular instance. Use
        ``instance.ports`` to inspect those points.
        """
        return cls.meta.describe_ports()

    @property
    def ports(self) -> tuple[Entity | PortHandle, ...]:
        """Concrete connection points and authored deferred ports on this entity.

        The authored model can contain both generated ConnectionPoint entities
        and PortHandle intentions. A resolved snapshot exposes concrete points
        here after the solver has materialized the deferred ones.
        """
        domain = self.meta.registry._domain
        return domain.ports(self) if domain is not None else ()

    def __enter__(self) -> Self:
        """Open a containment scope: entities created inside attach here."""
        _containment.push(self)
        return self

    def __exit__(self, *exc_info: object) -> None:
        _containment.pop(self)

    # -- operator sugar ---------------------------------------------------

    def __rshift__(self, other: Entity) -> Entity:
        """``a >> b``: the package-defined flow connection.

        Brick adds to the ``_RSHIFT`` property (``feeds``). S223/WaTr records
        a deferred intention for Z3 resolution. Returns ``b`` so chains read
        along the flow: ``a >> b >> c``. Use ``connect(a, b)`` when a stable
        handle is needed for a later medium hint.
        """
        if self._CONNECTOR is not None:
            self._CONNECTOR.connect(self, other)
            return other
        prop = self._RSHIFT
        if prop is None:
            raise TypeError(
                f"{type(self).__name__} does not participate in >> connections"
            )
        getattr(self, prop).add(other)
        return other

    def __lshift__(self, other: Entity) -> Entity:
        """``a << b``: mirror of ``>>`` (``b`` flows into ``a``).

        Also returns ``b``, so ``a << b << c`` reads against the flow.
        """
        if other._CONNECTOR is not None:
            other._CONNECTOR.connect(other, self)
            return other
        prop = other._RSHIFT
        if prop is None:
            raise TypeError(
                f"{type(other).__name__} does not participate in << connections"
            )
        getattr(other, prop).add(self)
        return other

    # -- internals --------------------------------------------------------

    @classmethod
    def _classinfo_effective(cls) -> ClassInfo:
        """The nearest ``_classinfo`` up the MRO (always exists for
        generated classes; Entity itself has none)."""
        for klass in cls.__mro__:
            info = klass.__dict__.get("_classinfo")
            if info is not None:
                return info
        raise TypeError(f"{cls.__name__} has no _classinfo")  # pragma: no cover

    @classmethod
    def _effective_specs(cls) -> dict[str, PropertySpec]:
        """name -> spec across the MRO; subclasses shadow parents by name.

        Cached per class (the spec set is fixed at generation time).
        """
        cached = cls.__dict__.get("_specs_cache")
        if cached is not None:
            return cached
        # Each declaration already contains its effective compiled constraint.
        # The MRO selects the nearest descriptor; it must not recompute range
        # intersections or reintroduce a broader inherited range. Look up the
        # cache in __dict__ so a subclass never borrows its parent's spec set.
        specs: dict[str, PropertySpec] = {}
        for klass in reversed(cls.__mro__):
            info = klass.__dict__.get("_classinfo")
            if info is not None:
                for spec in info.properties:
                    specs[spec.name] = spec
        cls._specs_cache = specs  # type: ignore[attr-defined]
        return specs

    def _store_for(self, spec: PropertySpec) -> RelSet[Any]:
        """The (lazily created) RelSet backing a multi-valued property."""
        store = self._rels.get(spec.name)
        if store is None:
            store = RelSet(self, spec)
            self._rels[spec.name] = store
        return store

    def _check_range(self, spec: PropertySpec, value: object) -> None:
        """Runtime mirror of the static range annotation."""
        from .terms import TermValue

        # External vocabulary classes are intentionally not always generated
        # as local Entity classes. A compiled named individual is then the
        # correct RDF object, rather than a newly minted local entity.
        registry = self.meta.registry
        allowed = tuple(registry.resolve(rng) for rng in spec.ranges)
        allowed_iris = {cls.meta.iri for cls in allowed}
        groups = spec.range_groups or (
            (tuple(sorted(allowed_iris)),) if allowed else ()
        )

        # A group is a union; the tuple of groups is a conjunction. For example,
        # ((Dog, Cat), (Tagged,)) means (Dog OR Cat) AND Tagged. Flattening this
        # into one list would silently accept untagged animals. RDF ancestry,
        # not the repaired Python MRO, decides membership in each group.
        def conforms(candidate: type[Entity] | TermValue) -> bool:
            return all(
                any(
                    any(
                        declared == iri
                        or (
                            (symbol := registry.by_iri.get(declared)) is not None
                            and symbol.meta.is_a(iri)
                        )
                        for declared in candidate.types
                    )
                    if isinstance(candidate, TermValue)
                    else candidate.meta.is_a(iri)
                    for iri in group
                )
                for group in groups
            )

        labels = [
            " | ".join(
                registry.by_iri[iri].__name__ if iri in registry.by_iri else iri
                for iri in group
            )
            for group in groups
        ]
        expected = " & ".join(
            f"({label})" if " | " in label and len(labels) > 1 else label
            for label in labels
        )
        if spec.kind == "class":
            if not isinstance(value, type) or not issubclass(value, Entity):
                raise RangeError(
                    f"{type(self).__name__}.{spec.name} expects an ontology "
                    f"class, got {value!r}"
                )
            if conforms(value):
                return
            raise RangeError(
                f"{type(self).__name__}.{spec.name} expects a subclass of "
                f"{expected}, got {value.__name__}"
            )
        if isinstance(value, TermValue):
            if conforms(value):
                return
            raise RangeError(
                f"{type(self).__name__}.{spec.name} expects {expected}, got "
                f"compiled term {value!r}"
            )
        if spec.deferred and self._check_deferred(spec, value):
            return
        if not isinstance(value, Entity):
            raise RangeError(
                f"{type(self).__name__}.{spec.name} links entities, got "
                f"{type(value).__name__} ({value!r})"
            )
        if not conforms(type(value)):
            raise RangeError(
                f"{type(self).__name__}.{spec.name} expects {expected}, got "
                f"{type(value).__name__} ({value.name!r})"
            )

    def _check_deferred(self, spec: PropertySpec, value: object) -> bool:
        """Accept a port, declared point, or connection handle of this model.

        Resolution replaces it with the concrete point or connection.
        """
        from .points import PointGroupRef, PointRef
        from .resolution import ConnectionHandle, PortHandle

        if isinstance(value, PointGroupRef):
            raise RangeError(
                f"{type(self).__name__}.{spec.name} needs one point; "
                f"{value.name!r} names a group, so pick one of its points"
            )
        if isinstance(value, PointRef):
            value = value._port
        if not isinstance(value, (PortHandle, ConnectionHandle)):
            return False
        if value._model is not self._model:
            raise RangeError(
                f"{type(self).__name__}.{spec.name}: {value.name!r} belongs to "
                "another Model"
            )
        return True

    def _apply_class_defaults(self) -> None:
        """Add each class-implied value the author did not already cover."""
        specs = self._effective_specs()
        for klass in type(self).__mro__:
            info = klass.__dict__.get("_classinfo")
            if info is None:
                continue
            for name, class_name in info.class_defaults:
                implied = info.registry.resolve(class_name)
                spec = specs[name]
                if spec.max_count == 1:
                    current = getattr(self, name)
                    if current is None:
                        setattr(self, name, implied)
                    continue
                store = self._store_for(spec)
                if not any(
                    isinstance(value, type) and issubclass(value, implied)
                    for value in store
                ):
                    store.add(implied)

    def _check_required(self) -> None:
        """Raise if any SHACL-required property is still empty."""
        missing: list[str] = []
        for spec in self._effective_specs().values():
            if not spec.required:
                continue
            if spec.kind in {"object", "class"} and spec.max_count != 1:
                if len(self._store_for(spec)) < max(1, spec.min_count):
                    missing.append(spec.name)
            elif spec.kind == "enum" and spec.max_count != 1:
                if len(self._data.get(spec.name, ())) < max(1, spec.min_count):
                    missing.append(spec.name)
            elif self._data.get(spec.name) is None:
                missing.append(spec.name)
        if missing:
            raise ModelingError(
                f"{type(self).__name__}({self.name!r}) is missing required "
                f"propert{'ies' if len(missing) > 1 else 'y'}: "
                f"{', '.join(missing)}"
            )

    def _property_values(self) -> Iterator[tuple[PropertySpec, Any]]:
        """Yield (spec, value) pairs for serialization of generated properties."""
        for spec in self._effective_specs().values():
            if spec.kind in {"object", "class"} and spec.max_count != 1:
                for target in self._store_for(spec):
                    yield spec, target
            elif spec.kind == "enum" and spec.max_count != 1:
                for value in self._data.get(spec.name) or ():
                    yield spec, value
            else:
                value = self._data.get(spec.name)
                if value is not None:
                    yield spec, value

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self._name!r}>"


def provided(**kwargs: Any) -> dict[str, Any]:
    """Filter constructor kwargs down to the ones the caller actually set.

    Generated ``__init__`` methods pass every parameter through this so that
    defaults (``None`` / ``()``) don't count as explicit assignments.
    """
    return {
        key: value for key, value in kwargs.items() if value is not None and value != ()
    }


def _mro_dicts(cls: type) -> dict[str, Any]:
    """Union of class __dict__s along the MRO (nearest wins)."""
    merged: dict[str, Any] = {}
    for klass in reversed(cls.__mro__):
        merged.update(klass.__dict__)
    return merged
