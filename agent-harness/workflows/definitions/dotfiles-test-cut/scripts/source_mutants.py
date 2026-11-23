import ast
import copy

COMPARISON_SWAPS = {
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Lt: ast.GtE,
    ast.GtE: ast.Lt,
    ast.Gt: ast.LtE,
    ast.LtE: ast.Gt,
    ast.In: ast.NotIn,
    ast.NotIn: ast.In,
    ast.Is: ast.IsNot,
    ast.IsNot: ast.Is,
}
BOOLEAN_SWAPS = {ast.And: ast.Or, ast.Or: ast.And}


def mutated_comparison(node):
    replacement = COMPARISON_SWAPS.get(type(node.ops[0]))
    if replacement is None:
        return None
    return ast.Compare(node.left, [replacement(), *node.ops[1:]], node.comparators)


def mutated_boolean_operation(node):
    return ast.BoolOp(BOOLEAN_SWAPS[type(node.op)](), node.values)


def mutated_constant(node):
    if isinstance(node.value, bool):
        return ast.Constant(not node.value)
    if isinstance(node.value, int):
        return ast.Constant(node.value + 1)
    if isinstance(node.value, str) and node.value:
        return ast.Constant(node.value + "~")
    return None


MUTATORS = {
    ast.Compare: mutated_comparison,
    ast.BoolOp: mutated_boolean_operation,
    ast.Constant: mutated_constant,
}


def mutation_of(node):
    mutator = MUTATORS.get(type(node))
    return None if mutator is None else mutator(node)


class SingleNodeReplacement(ast.NodeTransformer):
    def __init__(self, target_index):
        self.target_index = target_index
        self.visited_index = -1
        self.description = None

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Constant):
            return node
        return self.generic_visit(node)

    def generic_visit(self, node):
        replacement = mutation_of(node)
        if replacement is None:
            return super().generic_visit(node)
        self.visited_index += 1
        if self.visited_index != self.target_index:
            return super().generic_visit(node)
        self.description = (
            f"line {node.lineno}: {ast.unparse(node)} -> {ast.unparse(replacement)}"
        )
        return ast.copy_location(replacement, node)


def mutable_node_count(tree):
    return sum(1 for node in ast.walk(tree) if mutation_of(node) is not None)


def source_mutants(source_text, maximum_mutants):
    tree = ast.parse(source_text)
    total = mutable_node_count(tree)
    stride = max(1, -(-total // max(1, maximum_mutants)))
    mutants = []
    for target_index in range(0, total, stride):
        replacement = SingleNodeReplacement(target_index)
        mutated_tree = ast.fix_missing_locations(replacement.visit(copy.deepcopy(tree)))
        if replacement.description is not None:
            mutants.append((replacement.description, ast.unparse(mutated_tree)))
    return mutants
