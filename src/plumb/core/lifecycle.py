"""Core orchestration for optional domain planning and immutable snapshots."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol
from collections.abc import Iterator

if TYPE_CHECKING:
    from .entity import Entity
    from .traversal import Direction, Hop
    from .resolution import ConnectionHandle, PortHandle
    from .enums import EnumValue

from .errors import AmbiguousModelError, ModelingError, UnsatisfiableModelError
from .model import Model
from .resolution import ResolutionReport, ResolvedModel
from .snapshot import Snapshot


# Planning reads authored state; Plan.apply() writes only to the Snapshot build.
# Core checks the report before copying and publishes only a successful build.
class Plan(Protocol):
    """A domain decision that can populate a core-owned snapshot build."""

    @property
    def report(self) -> ResolutionReport: ...

    def apply(self, build: Snapshot) -> None: ...


class Domain(Protocol):
    """Internal vocabulary capabilities exercised by the generic runtime."""

    def plan(self, model: Model) -> Plan | None: ...
    def initialize(self, entity: Entity) -> None: ...
    def restore(self, entity: Entity, *, strict: bool) -> None: ...
    def finish_snapshot(self, model: Model) -> None: ...
    def owner(self, entity: Entity) -> Entity: ...
    def port(
        self,
        entity: Entity,
        name: str,
        *,
        direction: str,
        medium: EnumValue | None,
        label: str | None,
    ) -> PortHandle: ...
    def ports(self, entity: Entity) -> tuple[Entity | PortHandle, ...]: ...
    def boundary(self, entity: Entity, points: tuple[Any, ...]) -> None: ...
    def connection_type(self, handle: ConnectionHandle) -> type[Entity]: ...
    def check_mapping(self, port: PortHandle, target: object) -> None: ...
    def create_system(
        self, model: Model, name: str, label: str | None, candidates: list[Entity]
    ) -> Entity: ...
    def walk(
        self, start: Entity, direction: Direction, **options: Any
    ) -> Iterator[Hop]: ...


def domain_for(model: Model) -> Domain | None:
    """Select the capability shared by this model's generated classes."""
    # S223, WaTr, and their configurations must share the same _domain object.
    domains = {
        entity.meta.registry._domain
        for entity in model
        if entity.meta.registry._domain is not None
    }
    if len(domains) > 1:
        raise ModelingError("model contains incompatible resolution domains")
    if domains:
        return domains.pop()
    if model._connection_intents or model._port_intents:
        raise ModelingError("deferred connections require a connection domain")
    return None


def require_domain(entity: Entity) -> Domain:
    domain = entity.meta.registry._domain
    if domain is None:
        raise TypeError(f"{type(entity).__name__} has no connection-domain capability")
    return domain


def check_model(model: Model) -> ResolutionReport:
    """Report domain decisions without creating or changing model objects."""
    domain = domain_for(model)
    plan = domain.plan(model) if domain is not None else None
    return plan.report if plan is not None else ResolutionReport("complete")


def resolve_model(model: Model) -> ResolvedModel:
    """Plan first, then populate and freeze an isolated model copy."""
    domain = domain_for(model)
    plan = domain.plan(model) if domain is not None else None
    if plan is not None:
        report = plan.report
        message = "; ".join(issue.message for issue in report.issues)
        if report.status == "unsatisfiable":
            labels = tuple(label for issue in report.issues for label in issue.labels)
            raise UnsatisfiableModelError(
                f"{message}: {'; '.join(labels)}" if labels else message, core=labels
            )
        if report.status == "underconstrained":
            raise AmbiguousModelError(
                message, alternatives=tuple(issue.message for issue in report.issues)
            )
    build = Snapshot(model)
    if plan is not None:
        plan.apply(build)
    return build.finish()
