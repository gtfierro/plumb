"""Order-independent copies of ontology graphs.

rdflib iterates triples in insertion order and labels blank nodes randomly,
so the same imports closure loaded twice can yield differently ordered
generated code and shape bundles. :func:`stable_graph` relabels blank nodes
from their content and inserts triples in sorted order, which makes both
independent of how the input was assembled.

Full RDF canonicalization (``rdflib.compare``) is exact but too slow for
closures the size of Brick. Ontology blank nodes are almost always trees
(restrictions, property shapes, RDF lists), for which a content hash plus the
referencing context is already a stable label.
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict

import rdflib
from rdflib import RDF, BNode, Literal, URIRef
from rdflib.namespace import SH
from rdflib.term import Node

_PREFIX_CHARS = re.compile(r"[^A-Za-z0-9_-]")
_AUTO_PREFIX = re.compile(r"^(ns|default)\d+$")
_SOURCE_GROUP = re.compile(r"^(b[0-9a-f]{24})(?:_\d+)?$")


def source_id(node: rdflib.term.Node) -> str:
    """Identify an anonymous diagnostic source by its content/context group.

    Equal normalized nodes receive interchangeable numeric suffixes so they
    remain distinct RDF nodes. Those suffixes carry no stable diagnostic
    meaning; the report's target and path retain the source's scope.
    """
    label = str(node)
    if isinstance(node, BNode) and (match := _SOURCE_GROUP.fullmatch(label)):
        return match.group(1)
    return label


def stable_graph(graph: rdflib.Graph) -> rdflib.Graph:
    """Return a copy of ``graph`` whose iteration and serialization order
    depend only on its content."""
    graph = _normalize_prefix_declarations(graph)
    outgoing: dict[BNode, list[tuple[Node, Node]]] = defaultdict(list)
    incoming: dict[BNode, list[tuple[Node, Node]]] = defaultdict(list)
    for s, p, o in graph:
        if isinstance(s, BNode):
            outgoing[s].append((p, o))
        if isinstance(o, BNode):
            incoming[o].append((s, p))

    # Post-order over blank-node children, iteratively: RDF lists can be
    # longer than Python's recursion limit. A child still on the stack is a
    # cycle and contributes a fixed marker.
    content: dict[BNode, str] = {}

    def content_hash(root: BNode) -> str:
        stack: list[tuple[BNode, bool]] = [(root, False)]
        active: set[BNode] = set()
        while stack:
            node, expanded = stack.pop()
            if node in content:
                continue
            if not expanded:
                active.add(node)
                stack.append((node, True))
                for _p, o in outgoing[node]:
                    if isinstance(o, BNode) and o not in content and o not in active:
                        stack.append((o, False))
                continue
            parts = sorted(
                f"{p.n3()} " + _term_key(o, lambda b: content.get(b, "cycle"))
                for p, o in outgoing[node]
            )
            content[node] = hashlib.sha256("\n".join(parts).encode()).hexdigest()
            active.discard(node)
        return content[root]

    blank_nodes = set(outgoing) | set(incoming)
    labels: dict[BNode, str] = {}
    for node in blank_nodes:
        context = sorted(
            f"{_term_key(s, content_hash)} {p.n3()}" for s, p in incoming[node]
        )
        own = content_hash(node)
        labels[node] = hashlib.sha256(
            (own + "\n" + "\n".join(context)).encode()
        ).hexdigest()[:24]
    # Blank nodes with identical content and context are interchangeable;
    # numbering them in any order produces the same serialization.
    seen: dict[str, int] = defaultdict(int)
    relabel: dict[BNode, BNode] = {}
    for node in sorted(blank_nodes, key=lambda b: labels[b]):
        label = labels[node]
        seen[label] += 1
        suffix = "" if seen[label] == 1 else f"_{seen[label]}"
        relabel[node] = BNode(f"b{label}{suffix}")

    def mapped(term: Node) -> Node:
        return relabel[term] if isinstance(term, BNode) else term

    out = rdflib.Graph()
    for s, p, o in sorted((mapped(s), p, mapped(o)) for s, p, o in graph):
        out.add((s, p, o))
    _bind_stable_prefixes(out, graph)
    return out


def _normalize_prefix_declarations(graph: rdflib.Graph) -> rdflib.Graph:
    """Give each subject one unshared ``sh:declare`` node per prefix binding.

    Merging an imports closure (ontoenv's ``rewrite_sh_prefixes``) can share
    or duplicate declaration nodes differently on every run. SHACL reads only
    the (prefix, namespace) pairs, so this layout is equivalent.
    """
    declarations = list(graph.subject_objects(SH.declare))
    if not declarations and (None, SH.prefix, None) not in graph:
        return graph
    out = rdflib.Graph()
    for prefix, ns in graph.namespaces():
        out.bind(prefix, ns, override=False)
    # Declaration nodes referenced only through sh:declare, or orphaned by
    # the merge, are rebuilt below.
    dropped = {
        node
        for node in graph.subjects(SH.prefix, None)
        if isinstance(node, BNode)
        and (node, SH.namespace, None) in graph
        and all(p == SH.declare for _s, p in graph.subject_predicates(node))
    }
    for triple in graph:
        if triple[0] not in dropped and (
            triple[1] != SH.declare or not isinstance(triple[2], BNode)
        ):
            out.add(triple)
    pairs: set[tuple[Node, Node, Node]] = set()
    for subject, node in declarations:
        if not isinstance(node, BNode):
            continue
        prefix = graph.value(node, SH.prefix)
        namespace = graph.value(node, SH.namespace)
        if prefix is not None and namespace is not None:
            pairs.add((subject, prefix, namespace))
    for subject, prefix, namespace in sorted(pairs):
        node = BNode()
        out.add((subject, SH.declare, node))
        out.add((node, RDF.type, SH.PrefixDeclaration))
        out.add((node, SH.prefix, prefix))
        out.add((node, SH.namespace, namespace))
    return out


def _term_key(term: Node, blank) -> str:
    if isinstance(term, BNode):
        return "_:" + blank(term)
    if isinstance(term, (URIRef, Literal)):
        return term.n3()
    return str(term)


def _bind_stable_prefixes(out: rdflib.Graph, source: rdflib.Graph) -> None:
    """Carry over meaningful prefixes and name the rest deterministically."""
    declared = sorted(
        (str(ns), prefix)
        for prefix, ns in source.namespaces()
        if prefix and not _AUTO_PREFIX.match(prefix)
    )
    taken = {prefix for prefix, _ns in out.namespaces()}
    bound = {str(ns) for _prefix, ns in out.namespaces()}
    for ns, prefix in declared:
        if ns not in bound and prefix not in taken:
            out.bind(prefix, ns, override=False)
            taken.add(prefix)
            bound.add(ns)
    used: set[str] = set()
    for _s, p, o in out:
        for term in (p, o):
            if isinstance(term, URIRef):
                for sep in ("#", "/"):
                    if sep in term:
                        used.add(term.rsplit(sep, 1)[0] + sep)
                        break
    for ns in sorted(used - bound):
        segment = ns.rstrip("#/").rsplit("/", 1)[-1]
        stem = _PREFIX_CHARS.sub("", segment).lower().strip("-")
        if not stem or not stem[0].isalpha():
            stem = "ns"
        prefix, index = stem, 2
        while prefix in taken:
            prefix = f"{stem}{index}"
            index += 1
        out.bind(prefix, ns, override=False)
        taken.add(prefix)
