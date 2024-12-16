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
        self.original_word = None  # Store the original word without boundaries

class Trie:
    """
    Prefix tree that matches phrases with space/newline boundaries.
    """
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        """
        Insert word into trie with all possible boundary combinations.
        Stores original word without boundaries.
        """
        # Store variations with boundaries
        variations = [
            " " + word,
            word + " ",
            " " + word + " ",
            "\n" + word,
            word + "\n",
            "\n" + word + "\n"
        ]

        for variation in variations:
            node = self.root
            for char in variation.lower():
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
            node.is_end_of_word = True
            node.original_word = word.lower()  # Store original word without boundaries

    def find_names_in_document(self, document: str) -> set[str]:
        """
        Return set of original phrases (without boundaries) that appear in given document
        when surrounded by spaces or newlines.
        """
        found_names = set()

        # Add boundary characters to start and end for proper matching
        document = "\n" + document + "\n"
        document = document.lower()

        for i in range(len(document)):
            node = self.root
            j = i
            matched_name = None

            while j < len(document) and document[j] in node.children:
                node = node.children[document[j]]
                j += 1

                if node.is_end_of_word and node.original_word:
                    # Store the original word instead of the matched variation
                    matched_name = node.original_word

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
