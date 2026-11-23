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
ARITHMETIC_SWAPS = {
    ast.Add: ast.Sub,
    ast.Sub: ast.Add,
    ast.Mult: ast.Div,
    ast.Div: ast.Mult,
}


def mutated_comparison(node):
    replacement = COMPARISON_SWAPS.get(type(node.ops[0]))
    if replacement is None:
        return None
    return ast.Compare(node.left, [replacement(), *node.ops[1:]], node.comparators)


def mutated_boolean_operation(node):
    return ast.BoolOp(BOOLEAN_SWAPS[type(node.op)](), node.values)


def mutated_arithmetic(node):
    replacement = ARITHMETIC_SWAPS.get(type(node.op))
    if replacement is None:
        return None
    return ast.BinOp(node.left, replacement(), node.right)


def mutated_negation(node):
    return node.operand if isinstance(node.op, ast.Not) else None


def mutated_constant(node):
    if isinstance(node.value, bool):
        return ast.Constant(not node.value)
    if isinstance(node.value, int):
        return ast.Constant(node.value + 1)
    if isinstance(node.value, str) and node.value:
        return ast.Constant(node.value + "~")
    return None


def is_none(node):
    return node is None or (isinstance(node, ast.Constant) and node.value is None)


def mutated_return(node):
    return None if is_none(node.value) else ast.Return(ast.Constant(None))


def mutated_statement(node):
    return ast.Pass() if isinstance(node.value, (ast.Call, ast.Await)) else None


def mutated_raise(node):
    return ast.Pass()


MUTATORS = {
    ast.Compare: mutated_comparison,
    ast.BoolOp: mutated_boolean_operation,
    ast.BinOp: mutated_arithmetic,
    ast.UnaryOp: mutated_negation,
    ast.Constant: mutated_constant,
    ast.Return: mutated_return,
    ast.Expr: mutated_statement,
    ast.Raise: mutated_raise,
}


def mutation_of(node):
    mutator = MUTATORS.get(type(node))
    return None if mutator is None else mutator(node)


def is_documentation(node):
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)


class SingleNodeReplacement(ast.NodeTransformer):
    def __init__(self, target_index):
        self.target_index = target_index
        self.visited_index = -1
        self.line = None
        self.description = None

    def visit(self, node):
        if is_documentation(node):
            return node
        replacement = mutation_of(node)
        if replacement is None:
            return self.generic_visit(node)
        self.visited_index += 1
        if self.visited_index != self.target_index:
            return self.generic_visit(node)
        self.line = node.lineno
        self.description = (
            f"mutant {self.target_index} line {node.lineno}: "
            f"{ast.unparse(node)[:80]} -> {ast.unparse(replacement)[:80]}"
        )
        return ast.copy_location(replacement, node)


def mutable_node_count(tree):
    counting = SingleNodeReplacement(-1)
    counting.visit(copy.deepcopy(tree))
    return counting.visited_index + 1


def source_mutants(source_text, maximum_mutants):
    tree = ast.parse(source_text)
    total = mutable_node_count(tree)
    stride = max(1, -(-total // max(1, maximum_mutants)))
    mutants = []
    for target_index in range(0, total, stride):
        replacement = SingleNodeReplacement(target_index)
        mutated_tree = ast.fix_missing_locations(replacement.visit(copy.deepcopy(tree)))
        if replacement.description is not None:
            mutants.append(
                (replacement.line, replacement.description, ast.unparse(mutated_tree))
            )
    return mutants
