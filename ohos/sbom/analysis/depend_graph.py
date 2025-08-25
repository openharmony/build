from typing import List, Iterable, Tuple, Union, Optional, Callable

import networkx as nx
from networkx import DiGraph

from ohos.sbom.data.ninja_json import NinjaJson
from ohos.sbom.data.target import Target


class DependGraphAnalyzer:
    """
     Dependency graph service based on networkx.DiGraph
    """

    def __init__(self, src: Union[NinjaJson, List[Target]]) -> None:
        if isinstance(src, NinjaJson):
            targets = list(src.all_targets())
        elif isinstance(src, list):
            targets = src
        else:
            raise TypeError("src must be NinjaJson or List[Target]")

        self._graph = self._build_graph(targets)

    @property
    def graph(self) -> DiGraph:
        return self._graph

    def nodes(self) -> List[str]:
        return list(self._graph.nodes)

    def edges(self) -> List[Tuple[str, str]]:
        return list(self._graph.edges)

    def get_target(self, name: str) -> Target:
        return self._graph.nodes[name]["data"]

    def predecessors(self, name: str) -> List[str]:
        return list(self._graph.predecessors(name))

    def successors(self, name: str) -> List[str]:
        return list(self._graph.successors(name))

    def ancestors(self, name: str) -> List[str]:
        return list(nx.ancestors(self._graph, name))

    def descendants(self, name: str) -> List[str]:
        return list(nx.descendants(self._graph, name))

    def shortest_path(self, source: str, target: str) -> List[str]:
        return nx.shortest_path(self._graph, source, target)

    def sub_graph(self, nodes: Iterable[str]):
        return self._graph.subgraph(nodes).copy()

    def add_virtual_root(self, root_name: str, children: List[str]):
        virtual_target = type("VirtualTarget", (), {
            "target_name": root_name,
            "type": "virtual_root",
            "outputs": [],
            "source_outputs": {}
        })()
        self._graph.add_node(root_name, data=virtual_target)

        for child in children:
            if child not in self._graph:
                raise ValueError(f"virtual root '{child}' not exist in graph")
            self._graph.add_edge(root_name, child)

    def remove_virtual_root(self, root_name: str):
        if root_name in self._graph:
            self._graph.remove_node(root_name)

    def depend_subgraph(
            self,
            src: Union[str, Target],
            *,
            max_depth: int,
    ) -> DiGraph:

        if isinstance(src, Target):
            src = src.target_name
        if max_depth is None:
            max_depth = len(self._graph)
        return nx.ego_graph(self.graph, src, radius=max_depth, center=True, undirected=False)

    def dfs_downstream(
            self,
            start: Union[str, Target],
            max_depth: Optional[int] = None,
            pre_visit: Optional[Callable[[str, int, Optional[str]], bool]] = None,
            post_visit: Optional[Callable[[str, int, Optional[str]], None]] = None
    ) -> List[str]:
        """
        Perform depth-first traversal from the start point along downstream dependencies (successors)

        Parameters:
            start: traversal start point (target name or Target object)
            max_depth: maximum traversal depth (None means no limit)
            pre_visit: callback function before visiting a node
                Parameters: (current node name, current depth, parent node name)
                Return: bool - whether to continue traversing the node's children (False skips children)
            post_visit: callback function after visiting a node
                Parameters: (current node name, current depth, parent node name)

        Returns:
            List of nodes in traversal order
        """
        return self._dfs(
            start=start,
            neighbor_func=lambda n: self.successors(n),
            max_depth=max_depth,
            pre_visit=pre_visit,
            post_visit=post_visit
        )

    def dfs_upstream(
            self,
            start: Union[str, Target],
            max_depth: Optional[int] = None,
            pre_visit: Optional[Callable[[str, int, Optional[str]], bool]] = None,
            post_visit: Optional[Callable[[str, int, Optional[str]], None]] = None
    ) -> List[str]:
        return self._dfs(
            start=start,
            neighbor_func=lambda n: self.predecessors(n),
            max_depth=max_depth,
            pre_visit=pre_visit,
            post_visit=post_visit
        )

    def _dfs(
            self,
            start: Union[str, Target],
            neighbor_func: Callable[[str], List[str]],
            max_depth: Optional[int],
            pre_visit: Optional[Callable[[str, int, Optional[str]], bool]],
            post_visit: Optional[Callable[[str, int, Optional[str]], None]]
    ) -> List[str]:
        if isinstance(start, Target):
            start_name = start.target_name
        else:
            start_name = start
        if start_name not in self.nodes():
            raise ValueError(f"node {start_name} not exist in graph")

        visited = set()
        traversal_order = []
        stack = [(start_name, 0, None, False)]

        while stack:
            node, depth, parent, is_processed = stack.pop()

            if max_depth is not None and depth > max_depth:
                continue

            if not is_processed:
                if node in visited:
                    continue
                visited.add(node)
                traversal_order.append(node)

                continue_traverse = True
                if pre_visit is not None:
                    try:
                        continue_traverse = pre_visit(node, depth, parent)
                    except Exception as e:
                        raise RuntimeError(f"pre_visit execute failed: {e}") from e

                stack.append((node, depth, parent, True))

                if continue_traverse:
                    neighbors = neighbor_func(node)
                    for neighbor in reversed(neighbors):
                        if neighbor not in visited:
                            stack.append((neighbor, depth + 1, node, False))

            else:
                if post_visit is not None:
                    try:
                        post_visit(node, depth, parent)
                    except Exception as e:
                        raise RuntimeError(f"post_visit execute failed: {e}") from e

        return traversal_order

    @staticmethod
    def _build_graph(targets: List[Target]) -> DiGraph:
        g = nx.DiGraph()
        for t in targets:
            g.add_node(t.target_name, data=t)
        target_names = {t.target_name for t in targets}
        for t in targets:
            for dep in t.deps:
                if dep in target_names:
                    g.add_edge(t.target_name, dep)
        return g
