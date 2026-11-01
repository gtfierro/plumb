"""Render a resolved S223/WaTr model as a process flow sheet.

The layout is delegated to Graphviz's layered ``dot`` engine, which keeps the
main flow running left to right and never overlaps nodes or stream labels:

    from plumb import flowsheet

    sheet = flowsheet(model)        # displays inline in Jupyter
    sheet.save("plant.svg")         # or .png / .pdf / .dot
    print(sheet.source)             # the DOT text, no Graphviz needed

Connections become stream lines coloured by medium, labelled only with their
properties. Equipment with processes or treatment objectives is drawn as a
unit-operation box listing them; other equipment shows only its name and type.
Sensors and actuators are instrument bubbles beside what they observe or
actuate, and unconnected system boundary points become feed and product
terminals. Only S223 base classes are consulted, so any package built on S223
(WaTr and its domains included) renders without extra configuration.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from html import escape
from numbers import Number
from pathlib import Path
from typing import Any

from .core.entity import Entity
from .core.enums import EnumValue
from .core.model import Model
from .core.resolution import ResolvedModel
from .core.terms import TermValue

__all__ = ["Flowsheet", "flowsheet"]

_S223 = "http://data.ashrae.org/standard223#"
_FONT = "Helvetica"

#: Medium keyword (matched against the medium and its ancestors) -> line colour.
_MEDIUM_COLORS = (
    ("Sludge", "#8c564b"),
    ("Wastewater", "#7f6a3a"),
    ("Water", "#1f77b4"),
    ("Air", "#7f7f7f"),
    ("Steam", "#d62728"),
    ("Gas", "#bcbd22"),
    ("Electricity", "#ff7f0e"),
    ("Chemical", "#9467bd"),
)
_DEFAULT_COLOR = "#444444"

#: Sensor class local name -> ISA-style instrument tag.
_SENSOR_TAGS = {
    "FlowSensor": "FT",
    "LevelSensor": "LT",
    "PressureSensor": "PT",
    "DifferentialPressureSensor": "PDT",
    "TemperatureSensor": "TT",
    "HumiditySensor": "MT",
    "ConductivitySensor": "CT",
    "TurbidityMeter": "AT",
    "ConcentrationSensor": "AT",
    "FrequencySensor": "ST",
    "VolumeSensor": "LT",
    "ElectricCurrentSensor": "IT",
    "ElectricVoltageSensor": "ET",
    "OccupantCountSensor": "QT",
}


class Flowsheet:
    """A rendered-on-demand flow sheet; ``source`` holds the Graphviz DOT."""

    def __init__(self, source: str) -> None:
        self.source = source

    def render(self, format: str = "svg") -> bytes:
        """Lay out the sheet with Graphviz ``dot`` and return the output."""
        executable = shutil.which("dot")
        if executable is None:
            raise RuntimeError(
                "rendering a flowsheet needs Graphviz's `dot` on PATH "
                "(e.g. `brew install graphviz` or `apt install graphviz`); "
                "Flowsheet.source holds the DOT text"
            )
        result = subprocess.run(
            [executable, f"-T{format}"],
            input=self.source.encode(),
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"dot failed: {result.stderr.decode().strip()}")
        return result.stdout

    def save(self, path: str | Path) -> Path:
        """Write the sheet; the suffix picks the format (``.dot`` is the source)."""
        path = Path(path)
        format = path.suffix.lstrip(".").lower() or "svg"
        if format in {"dot", "gv"}:
            path.write_text(self.source)
        else:
            path.write_bytes(self.render(format))
        return path

    def _repr_svg_(self) -> str | None:
        if shutil.which("dot") is None:
            return None
        return self.render("svg").decode()

    def __repr__(self) -> str:
        return f"<Flowsheet: {self.source.count(' -> ')} lines>"


def flowsheet(
    model: Model | ResolvedModel,
    *,
    title: str | None = None,
    properties: bool = True,
    instruments: bool = True,
    legend: bool = True,
    direction: str = "LR",
) -> Flowsheet:
    """Draw ``model`` as a flow sheet.

    An authored :class:`Model` is resolved first, so deferred connections and
    points appear as the solver placed them. ``properties`` lists equipment and
    stream properties, ``instruments`` adds sensors and actuators, and
    ``direction`` is the Graphviz rank direction (``"LR"`` or ``"TB"``).
    """
    entities = list(model.resolve() if isinstance(model, Model) else model)
    return Flowsheet(
        _Builder(
            entities,
            properties=properties,
            instruments=instruments,
        ).dot(title=title, legend=legend, direction=direction)
    )


# --- classification -----------------------------------------------------------


def _class_iris(entity: Entity) -> set[str]:
    return {
        cls.__dict__["_classinfo"].iri
        for cls in type(entity).__mro__
        if "_classinfo" in cls.__dict__
    }


def _is(entity: Entity, local: str) -> bool:
    return _S223 + local in _class_iris(entity)


def _many(entity: object, attribute: str) -> list[Any]:
    value = getattr(entity, attribute, None)
    if value is None:
        return []
    if isinstance(value, (Entity, EnumValue, TermValue, type, str, Number)):
        return [value]
    return list(value)


def _one(entity: object, attribute: str) -> Any:
    values = _many(entity, attribute)
    return values[0] if values else None


def _local(iri: str) -> str:
    return re.split(r"[#/]", iri)[-1]


def _term_text(value: Any) -> str:
    """Human-readable text for a class, enum, vocabulary term, or entity."""
    if isinstance(value, type) and issubclass(value, Entity):
        return value.meta.label or value.__name__
    if isinstance(value, EnumValue):
        return value.label or _local(value.iri)
    if isinstance(value, TermValue):
        return getattr(value, "symbol", None) or _local(value.iri)
    if isinstance(value, Entity):
        return value.name
    return str(value)


def _value_text(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, Number):
        return format(value, ",g")
    return _term_text(value)


def _class_label(entity: Entity) -> str:
    cls = type(entity)
    return cls.meta.label or re.sub(r"(?<!^)(?=[A-Z])", " ", cls.__name__)


def _medium_color(medium: Any) -> str:
    if not isinstance(medium, EnumValue):
        return _DEFAULT_COLOR
    lineage: list[str] = []
    pending = [medium]
    while pending:
        value = pending.pop(0)
        lineage.append(_local(value.iri))
        pending.extend(value.parents)
    for keyword, color in _MEDIUM_COLORS:
        if any(keyword in name for name in lineage):
            return color
    return _DEFAULT_COLOR


def _sensor_tag(sensor: Entity) -> str:
    for cls in type(sensor).__mro__:
        tag = _SENSOR_TAGS.get(cls.__name__)
        if tag is not None:
            return tag
    return "XT"


# --- DOT construction ---------------------------------------------------------


def _q(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _attrs(**values: str | None) -> str:
    parts = []
    for key, value in values.items():
        if value is None:
            continue
        if value.startswith("<") and value.endswith(">"):
            parts.append(f"{key}={value}")
        else:
            parts.append(f"{key}={_q(value)}")
    return "[" + ", ".join(parts) + "]"


def _row(text: str, *, size: int = 10, color: str = "#222222", **cell: str) -> str:
    extra = "".join(f' {key.upper()}="{value}"' for key, value in cell.items())
    return (
        f'<TR><TD ALIGN="LEFT" BALIGN="LEFT"{extra}>'
        f'<FONT POINT-SIZE="{size}" COLOR="{color}">{text}</FONT></TD></TR>'
    )


@dataclass
class _Cluster:
    system: Entity | None
    lines: list[str] = field(default_factory=list)
    children: list[_Cluster] = field(default_factory=list)


class _Builder:
    def __init__(
        self,
        entities: Iterable[Entity],
        *,
        properties: bool,
        instruments: bool,
    ) -> None:
        self.entities = list(entities)
        self.show_properties = properties
        self.show_instruments = instruments
        self.ids: dict[int, str] = {}
        self.owner: dict[int, Entity] = {}
        self.point_connection: dict[int, Entity] = {}
        self.junctions: dict[int, str] = {}
        self.media: dict[str, str] = {}
        self.edges: list[str] = []

        self.equipment = [
            entity
            for entity in self.entities
            if _is(entity, "Connectable")
            and not (_is(entity, "Sensor") or _is(entity, "Actuator"))
        ]
        self.sensors = [e for e in self.entities if _is(e, "Sensor")]
        self.actuators = [e for e in self.entities if _is(e, "Actuator")]
        self.connections = [e for e in self.entities if _is(e, "Connection")]
        self.systems = [e for e in self.entities if _is(e, "System")]
        for equipment in self.equipment:
            for point in _many(equipment, "has_connection_point"):
                self.owner[id(point)] = equipment
        for connection in self.connections:
            for point in _many(connection, "connects_at"):
                self.point_connection[id(point)] = connection
        # Properties a sensor observes or an actuator commands are shown on
        # the instrument, not repeated in the box or stream label.
        self.instrumented: set[int] = set()
        if self.show_instruments:
            for sensor in self.sensors:
                self.instrumented.update(id(p) for p in _many(sensor, "observes"))
            for actuator in self.actuators:
                self.instrumented.update(
                    id(p) for p in _many(actuator, "actuated_by_property")
                )
            for equipment in self.equipment:
                self.instrumented.update(
                    id(p) for p in _many(equipment, "actuated_by_property")
                )

    def node_id(self, entity: Entity) -> str:
        return self.ids.setdefault(id(entity), f"n{len(self.ids)}")

    # -- clusters

    def clusters(self) -> tuple[_Cluster, dict[int, _Cluster]]:
        """Nest systems as clusters; each equipment joins its first system."""
        root = _Cluster(None)
        by_system: dict[int, _Cluster] = {}
        placement: dict[int, _Cluster] = {}
        nested = {
            id(member)
            for system in self.systems
            for member in _many(system, "has_member")
            if _is(member, "System")
        }

        def place(system: Entity, parent: _Cluster) -> None:
            if id(system) in by_system:
                return
            cluster = _Cluster(system)
            by_system[id(system)] = cluster
            parent.children.append(cluster)
            for member in _many(system, "has_member"):
                if _is(member, "System"):
                    place(member, cluster)
                else:
                    placement.setdefault(id(member), cluster)

        for system in self.systems:
            if id(system) not in nested:
                place(system, root)
        return root, placement

    # -- nodes

    def property_rows(self, subject: Entity) -> list[str]:
        if not self.show_properties:
            return []
        rows = []
        for prop in _many(subject, "has_property"):
            if id(prop) in self.instrumented:
                continue
            value = _one(prop, "has_value")
            if value is None:
                continue
            text = _value_text(value)
            unit = _one(prop, "has_unit")
            if unit is not None and _local(unit.iri) != "UNITLESS":
                text += f" {_term_text(unit)}"
            label = prop.label if prop.label != prop.name else prop.name
            rows.append(
                _row(f"{escape(label)} = <B>{escape(text)}</B>", size=9, color="#333")
            )
        return rows

    def equipment_node(self, equipment: Entity) -> str:
        processes = _many(equipment, "has_process")
        objectives = _many(equipment, "has_treatment_objective")
        roles = _many(equipment, "has_role")
        header = (
            f'<TR><TD ALIGN="CENTER"><B><FONT POINT-SIZE="12">'
            f"{escape(equipment.name)}</FONT></B></TD></TR>"
            f'<TR><TD ALIGN="CENTER"><I><FONT POINT-SIZE="9" COLOR="#555555">'
            f"{escape(_class_label(equipment))}</FONT></I></TD></TR>"
        )
        body: list[str] = []
        if processes or objectives:
            if processes:
                body.append(_row("<B>Processes</B>", size=9, color="#555555"))
                body.extend(
                    _row(f"• {escape(_term_text(p))}", size=10) for p in processes
                )
            if objectives:
                body.append(_row("<B>Objectives</B>", size=9, color="#555555"))
                body.extend(
                    _row(f"• {escape(_term_text(o))}", size=10) for o in objectives
                )
        if roles:
            body.append(
                _row(
                    "role: " + escape(", ".join(_term_text(r) for r in roles)),
                    size=9,
                    color="#555555",
                )
            )
        body.extend(self.property_rows(equipment))
        unit_operation = bool(processes or objectives)
        if body:
            separator = "<HR/>" if unit_operation else ""
            table = header + separator + "".join(body)
        else:
            table = header
        label = (
            '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">'
            f"{table}</TABLE>>"
        )
        tank = any(cls.__name__ == "Tank" for cls in type(equipment).__mro__)
        if unit_operation:
            style = _attrs(
                shape="box",
                style="filled",
                fillcolor="#eef4fb",
                color="#2b5d8a",
                penwidth="1.5",
                label=label,
                margin="0.15,0.08",
            )
        elif _is(equipment, "Junction"):
            style = _attrs(
                shape="box",
                style="rounded,filled",
                fillcolor="#ffffff",
                color="#555555",
                label=label,
                margin="0.06,0.02",
            )
        else:
            style = _attrs(
                shape="cylinder" if tank else "box",
                style="rounded,filled" if not tank else "filled",
                fillcolor="#f7f7f7",
                color="#555555",
                label=label,
                margin="0.12,0.05",
            )
        return f"{self.node_id(equipment)} {style};"

    def terminal_node(self, point: Entity) -> str:
        medium = _one(point, "has_medium") or _one(point, "medium")
        lines = [f"<B>{escape(point.name)}</B>"]
        if medium is not None:
            lines.append(
                f'<FONT POINT-SIZE="9" COLOR="#555555">'
                f"{escape(_term_text(medium))}</FONT>"
            )
        label = "<" + "<BR/>".join(lines) + ">"
        return (
            f"{self.node_id(point)} "
            + _attrs(
                shape="cds",
                style="filled",
                fillcolor="#fff8e1",
                color="#a07c00",
                label=label,
                fontsize="10",
            )
            + ";"
        )

    # -- streams

    def stream_label(self, connection: Entity) -> str | None:
        # Stream names stay in the tooltip; only properties are drawn.
        rows = self.property_rows(connection)
        if not rows:
            return None
        return (
            '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1"'
            ' BGCOLOR="#ffffffcc">' + "".join(rows) + "</TABLE>>"
        )

    def endpoint(self, point: Entity) -> str | None:
        owner = self.owner.get(id(point))
        return self.node_id(owner) if owner is not None else None

    def stream_edges(self, connection: Entity) -> None:
        points = _many(connection, "connects_at")
        sources = [p for p in points if _is(p, "OutletConnectionPoint")]
        targets = [p for p in points if _is(p, "InletConnectionPoint")]
        others = [p for p in points if p not in sources and p not in targets]
        # Bidirectional point order determines drawing orientation only.
        if not sources and others:
            sources.append(others.pop(0))
        targets.extend(others)
        medium = _one(connection, "medium") or _one(connection, "has_medium")
        color = _medium_color(medium)
        if medium is not None:
            self.media[_term_text(medium)] = color
        line = {"color": color, "penwidth": "1.8", "arrowsize": "0.8"}
        label = self.stream_label(connection)
        tooltip = connection.name + (
            f" ({_term_text(medium)})" if medium is not None else ""
        )
        tails = [self.endpoint(p) for p in sources]
        heads = [self.endpoint(p) for p in targets]
        tails = [t for t in tails if t]
        heads = [h for h in heads if h]
        if not tails or not heads:
            return
        if len(tails) == 1 and len(heads) == 1 and id(connection) not in self.junctions:
            self.edges.append(
                f"{tails[0]} -> {heads[0]} "
                + _attrs(label=label, tooltip=tooltip, **line)
                + ";"
            )
            return
        # Several branches, or an instrument on the line: route the stream
        # through a junction so the instrument (or branches) can attach to it.
        junction = self.junction(connection)
        for index, tail in enumerate(tails):
            self.edges.append(
                f"{tail} -> {junction} "
                + _attrs(
                    arrowhead="none",
                    label=label if index == 0 else None,
                    tooltip=tooltip,
                    **line,
                )
                + ";"
            )
        for head in heads:
            self.edges.append(
                f"{junction} -> {head} " + _attrs(tooltip=tooltip, **line) + ";"
            )

    def junction(self, connection: Entity) -> str:
        return self.junctions.setdefault(id(connection), f"j{len(self.junctions)}")

    # -- instruments

    def location_anchor(self, sensor: Entity) -> str | None:
        location = _one(sensor, "has_observation_location")
        if location is None:
            return None
        if _is(location, "Connection"):
            return self.junction(location)
        if _is(location, "ConnectionPoint"):
            connection = self.point_connection.get(id(location))
            if connection is not None:
                return self.junction(connection)
            owner = self.owner.get(id(location))
            return self.node_id(owner) if owner is not None else None
        if id(location) in {id(e) for e in self.equipment}:
            return self.node_id(location)
        return None

    def instrument_label(self, tag: str, entity: Entity, detail: str) -> str:
        return (
            f'<<FONT POINT-SIZE="11"><B>{escape(tag)}</B></FONT><BR/>'
            f'<FONT POINT-SIZE="8">{escape(entity.name)}</FONT><BR/>'
            f'<FONT POINT-SIZE="7" COLOR="#555555">{escape(detail)}</FONT>>'
        )

    def quantity_detail(self, prop: Entity | None) -> str:
        if prop is None:
            return ""
        kind = _one(prop, "has_quantity_kind") or _one(prop, "has_enumeration_kind")
        unit = _one(prop, "has_unit")
        parts = [_term_text(kind)] if kind is not None else []
        if unit is not None:
            parts.append(_term_text(unit))
        return " · ".join(parts)

    def instruments(self) -> Iterator[tuple[str, str, str]]:
        """Yield ``(anchor, node line, link line)`` for each instrument."""
        if not self.show_instruments:
            return
        for sensor in self.sensors:
            anchor = self.location_anchor(sensor)
            if anchor is None:
                continue
            node = self.node_id(sensor)
            label = self.instrument_label(
                _sensor_tag(sensor),
                sensor,
                self.quantity_detail(_one(sensor, "observes")),
            )
            yield (
                anchor,
                f"{node} "
                + _attrs(
                    shape="ellipse",
                    style="filled",
                    fillcolor="#ffffff",
                    color="#333333",
                    label=label,
                    margin="0.04,0.02",
                    tooltip=_class_label(sensor),
                )
                + ";",
                f"{anchor} -> {node} "
                + _attrs(
                    style="dashed",
                    dir="none",
                    color="#666666",
                    minlen="1",
                    weight="0",
                )
                + ";",
            )
        for actuator in self.actuators:
            for target in _many(actuator, "actuates"):
                if id(target) not in {id(e) for e in self.equipment}:
                    continue
                anchor = self.node_id(target)
                node = self.node_id(actuator)
                command = _one(actuator, "actuated_by_property")
                label = self.instrument_label(
                    "ZC", actuator, self.quantity_detail(command)
                )
                yield (
                    anchor,
                    f"{node} "
                    + _attrs(
                        shape="box",
                        style="rounded,filled,dashed",
                        fillcolor="#ffffff",
                        color="#333333",
                        label=label,
                        margin="0.06,0.02",
                        tooltip=_class_label(actuator),
                    )
                    + ";",
                    f"{node} -> {anchor} "
                    + _attrs(
                        style="dashed",
                        color="#666666",
                        arrowsize="0.6",
                        weight="0",
                    )
                    + ";",
                )
                break

    # -- assembly

    def dot(self, *, title: str | None, legend: bool, direction: str) -> str:
        root, placement = self.clusters()

        def home(entity: Entity) -> _Cluster:
            return placement.get(id(entity), root)

        for equipment in self.equipment:
            home(equipment).lines.append(self.equipment_node(equipment))

        # Instruments decide which streams need a junction, so collect first.
        instruments = list(self.instruments())
        for connection in self.connections:
            self.stream_edges(connection)
        junction_home: dict[str, _Cluster] = {}
        for connection in self.connections:
            junction = self.junctions.get(id(connection))
            if junction is None:
                continue
            owners = {
                id(home(self.owner[id(p)]))
                for p in _many(connection, "connects_at")
                if id(p) in self.owner
            }
            clusters = [
                home(self.owner[id(p)])
                for p in _many(connection, "connects_at")
                if id(p) in self.owner
            ]
            cluster = clusters[0] if len(owners) == 1 else root
            junction_home[junction] = cluster
            cluster.lines.append(
                f"{junction} "
                + _attrs(
                    shape="point",
                    width="0.06",
                    color="#333333",
                    tooltip=connection.name,
                )
                + ";"
            )

        anchor_home = {
            self.node_id(equipment): home(equipment) for equipment in self.equipment
        }
        anchor_home.update(junction_home)
        grouped: dict[str, list[str]] = {}
        for anchor, node, link in instruments:
            cluster = anchor_home.get(anchor, root)
            cluster.lines.append(node)
            grouped.setdefault(anchor, []).append(node.split(" ", 1)[0])
            self.edges.append(link)
        for anchor, nodes in grouped.items():
            # Same rank as the anchor puts the bubble beside the line or box,
            # where a flow sheet draws it, instead of downstream of it.
            anchor_home.get(anchor, root).lines.append(
                "{rank=same; " + "; ".join([anchor, *nodes]) + ";}"
            )

        self.terminals(root)

        lines = [
            "digraph flowsheet {",
            f"  graph {_attrs(rankdir=direction, fontname=_FONT, nodesep='0.35', ranksep='0.55', newrank='true', splines='spline', pad='0.3', bgcolor='white')};",
            f"  node {_attrs(fontname=_FONT, fontsize='10')};",
            f"  edge {_attrs(fontname=_FONT, fontsize='9')};",
        ]
        graph_label = self.graph_label(title, legend)
        if graph_label:
            lines.append(
                f"  graph {_attrs(label=graph_label, labelloc='b', labeljust='l')};"
            )
        lines.extend(self.cluster_lines(root, depth=1))
        lines.extend(f"  {edge}" for edge in self.edges)
        lines.append("}")
        return "\n".join(lines) + "\n"

    def terminals(self, root: _Cluster) -> None:
        """Add feed and product terminals for unconnected boundary points."""
        seen: set[int] = set()
        for system in self.systems:
            for point in _many(system, "has_boundary_connection_point"):
                if id(point) in seen or id(point) in self.point_connection:
                    continue
                seen.add(id(point))
                owner = self.owner.get(id(point))
                if owner is None:
                    continue
                inbound = not _is(point, "OutletConnectionPoint")
                root.lines.append(self.terminal_node(point))
                medium = _one(point, "has_medium") or _one(point, "medium")
                color = _medium_color(medium)
                if medium is not None:
                    self.media[_term_text(medium)] = color
                line = _attrs(color=color, penwidth="1.8", arrowsize="0.8")
                terminal = self.node_id(point)
                if inbound:
                    self.edges.append(f"{terminal} -> {self.node_id(owner)} {line};")
                else:
                    self.edges.append(f"{self.node_id(owner)} -> {terminal} {line};")

    def graph_label(self, title: str | None, legend: bool) -> str | None:
        rows = []
        if title:
            rows.append(
                f'<TR><TD ALIGN="LEFT" COLSPAN="2"><B><FONT POINT-SIZE="14">'
                f"{escape(title)}</FONT></B></TD></TR>"
            )
        if legend and self.media:
            for name, color in sorted(self.media.items()):
                rows.append(
                    f'<TR><TD WIDTH="28" HEIGHT="10" FIXEDSIZE="TRUE">'
                    f'<FONT COLOR="{color}" POINT-SIZE="14">━━</FONT></TD>'
                    f'<TD ALIGN="LEFT"><FONT POINT-SIZE="9">{escape(name)}'
                    f"</FONT></TD></TR>"
                )
        if not rows:
            return None
        return (
            '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">'
            + "".join(rows)
            + "</TABLE>>"
        )

    def cluster_lines(self, cluster: _Cluster, depth: int) -> list[str]:
        indent = "  " * depth
        lines = [f"{indent}{line}" for line in cluster.lines]
        for child in cluster.children:
            assert child.system is not None
            name = f"cluster_{self.node_id(child.system)}"
            lines.append(f"{indent}subgraph {name} {{")
            lines.append(
                f"{indent}  graph "
                + _attrs(
                    label=f"<<B>{escape(child.system.name)}</B>>",
                    style="dashed,rounded",
                    color="#999999",
                    labeljust="l",
                    fontsize="11",
                )
                + ";"
            )
            lines.extend(self.cluster_lines(child, depth + 1))
            lines.append(f"{indent}}}")
        return lines
