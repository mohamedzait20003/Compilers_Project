from graphviz import Digraph
from parser import SyntaxTreeNode

class TreeVisualizer:
    def __init__(self, rankdir='LR', comment="TINY Syntax Tree"):
        self.rankdir = rankdir
        self.comment = comment
        self.node_counter = 0 

    def _get_node_id(self):
        node_id = f"node{self.node_counter}"
        self.node_counter += 1
        return node_id

    def _add_nodes_edges(self, dot, node, parent_id=None):
        current_id = self._get_node_id()

        is_keyword_like = not node.label.islower() and not node.label.startswith('assign (') and not node.label.startswith('read (') and not node.label.startswith('const (') and not node.label.startswith('id (') and not node.label.startswith('OP (')
        
        if node.label in ['program', 'stmt_seq', 'if', 'repeat', 'assign', 'read', 'write', 'OP']:
             shape = "ellipse"
             color = "plum1" 
        elif node.label.islower() and node.label not in ['if', 'then', 'else', 'end', 'repeat', 'until', 'read', 'write']: 
            shape = "ellipse"
            color = "skyblue"
        elif any(k_word in node.label for k_word in ['assign (', 'read (', 'const (', 'id (', 'OP (']): 
            shape = "box"
            color = "lightgoldenrod1" 
        else: 
            shape = "box"
            color = "palegreen" 

        dot.node(current_id, label=str(node.label), shape=shape, style="filled", fillcolor=color)

        if parent_id is not None:
            dot.edge(parent_id, current_id)

        for child in node.children:
            self._add_nodes_edges(dot, child, current_id)

    def render_tree(self, root: SyntaxTreeNode):
        if not isinstance(root, SyntaxTreeNode):
            print("Error: Root node is not a valid SyntaxTreeNode.")
            return None
        try:
            self.node_counter = 0 
            dot = Digraph(comment=self.comment)
            dot.attr(rankdir=self.rankdir)
            
            self._add_nodes_edges(dot, root)
            return dot

        except Exception as e:
            print(f"Error creating syntax tree: {str(e)}")
            return None
