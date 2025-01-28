import collections

#################################################################################################################################################
#################################################################################################################################################

class DirectedGraph:
    """
    Adjacency list for a directed graph.
    In degree values stored separately for faster access.
    """
    def __init__(self):
        self.adj = collections.defaultdict(set)
        self.in_degrees = collections.defaultdict(int)

    def add_vertex(self, vertex: str) -> None:
        if vertex not in self.adj:
            self.adj[vertex] = set()

        if vertex not in self.in_degrees:
            self.in_degrees[vertex] = 0

    def add_edge(self, from_vertex: str, to_vertex: str) -> None:
        self.adj[from_vertex].add(to_vertex)
        if to_vertex not in self.adj:
            self.adj[to_vertex] = set()

        if to_vertex not in self.in_degrees:
            self.in_degrees[to_vertex] = 0
        self.in_degrees[to_vertex] += 1

    def get_in_edges(self, to_vertex: str) -> set:
        in_edges = set()
        for from_vertex, to_vertices in self.adj.items():
            if to_vertex in to_vertices:
                in_edges.add((from_vertex, to_vertex))
        return in_edges

    def print_graph(self) -> None:
        if not self.adj:
            print("Graph is empty!")
            return

        print("Graph:")
        for from_vertex in sorted(self.adj.keys()):
            print(f"    {from_vertex}: {sorted(self.adj[from_vertex])}")

        print("\n", end="")
        print("In degrees:")
        for vertex in sorted(self.in_degrees.keys()):
            print(f"    {vertex}: {self.in_degrees[vertex]}")


#################################################################################################################################################
#################################################################################################################################################

class TrieNode:
    """
    Prefix tree node.
    """
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    """
    Prefix tree.
    """
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def find_names_in_document(self, document: str) -> set[str]:
        """
        Return set of names from prefix tree that appear in given document.
        """
        document = document.lower()
        found_names = set()

        for i in range(len(document)):
            if i > 0 and document[i-1].isalnum():
                continue

            node = self.root
            j = i

            matched_name = None

            while j < len(document) and document[j] in node.children:
                node = node.children[document[j]]
                j += 1

                if node.is_end_of_word:
                    if j == len(document) or not document[j].isalnum():
                        matched_name = document[i:j]

            if matched_name:
                found_names.add(matched_name)

        return found_names

    def get_all_words(self) -> list[str]:
        """
        Return all words stored in the prefix tree.
        """
        words = []
        def dfs(node: TrieNode, current_word: str) -> None:
            if node.is_end_of_word:
                words.append(current_word)

            for char, child in node.children.items():
                dfs(child, current_word + char)

        dfs(self.root, "")
        return sorted(words)

#################################################################################################################################################
#################################################################################################################################################

class ProgressCounter:
    """
    Simple class for progress bar prints.
    """
    def __init__(self, i: int, total: int):
        self.i = i
        self.total = total

    def increment(self) -> None:
        self.i += 1

    def print_progress_bar(self) -> None:
        progress = self.i / self.total
        bar_length = 30
        filled_length = int(bar_length * progress)
        bar = "=" * filled_length + "-" * (bar_length - filled_length)
        percent = progress * 100
        print(f"\rProgress: [{bar}] {percent:.1f}% ({self.i}/{self.total})", end="", flush=True)

#################################################################################################################################################
#################################################################################################################################################
