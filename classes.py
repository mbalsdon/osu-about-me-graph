import collections

#################################################################################################################################################
#################################################################################################################################################

class UndirectedGraph:
    """
    Adjacency list for an undirected graph.
    """
    def __init__(self):
        self.adj = collections.defaultdict(set)

    def add_edge(self, u: str, v: str) -> None:
        self.adj[u].add(v)
        self.adj[v].add(u)

    def print_graph(self) -> None:
        if not self.adj:
            print("Graph is empty!")
            return

        print("Graph:")
        vertices = sorted(self.adj.keys())
        for vertex in vertices:
            neighbors = sorted(self.adj[vertex])
            print(f"    {vertex}: {neighbors}")

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
