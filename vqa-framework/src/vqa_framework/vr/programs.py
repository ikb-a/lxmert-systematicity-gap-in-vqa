#!/usr/bin/env python3

# This code is released under the MIT License in association with the following paper:
#
# CLOSURE: Assessing Systematic Generalization of CLEVR Models (https://arxiv.org/abs/1912.05783).
#
# Full copyright and license information (including third party attribution) in the NOTICE file (https://github.com/rizar/CLOSURE/NOTICE).

"""
Utilities for working with and converting between the various data structures
used to represent programs.
"""


class ProgramConverter(object):
    def __init__(self, vocab=None):
        """
        `vocab` is necessary only for prefix_to_list, cause in this case
        we need to know the arity of the tokens.
        """
        self._vocab = vocab

    def is_chain(self, program_list):
        visited = [False for fn in program_list]
        cur_idx = len(program_list) - 1
        while True:
            visited[cur_idx] = True
            inputs = program_list[cur_idx]["inputs"]
            if len(inputs) == 0:
                break
            elif len(inputs) == 1:
                cur_idx = inputs[0]
            elif len(inputs) > 1:
                return False
        return all(visited)

    def list_to_tree(self, program_list):
        def build_subtree(cur):
            return {
                "function": cur["function"],
                "value_inputs": [x for x in cur["value_inputs"]],
                "inputs": [build_subtree(program_list[i]) for i in cur["inputs"]],
            }

        return build_subtree(program_list[-1])

    def tree_to_prefix(self, program_tree):
        output = []

        def helper(cur):
            output.append(
                {
                    "function": cur["function"],
                    "value_inputs": [x for x in cur["value_inputs"]],
                }
            )
            for node in cur["inputs"]:
                helper(node)

        helper(program_tree)
        return output

    def list_to_prefix(self, program_list):
        return self.tree_to_prefix(self.list_to_tree(program_list))

    def tree_to_postfix(self, program_tree):
        output = []

        def helper(cur):
            for node in cur["inputs"]:
                helper(node)
            output.append(
                {
                    "function": cur["function"],
                    "value_inputs": [x for x in cur["value_inputs"]],
                }
            )

        helper(program_tree)
        return output

    def tree_to_list(self, program_tree):
        # First count nodes
        def count_nodes(cur):
            return 1 + sum(count_nodes(x) for x in cur["inputs"])

        num_nodes = count_nodes(program_tree)
        output = [None] * num_nodes

        def helper(cur, idx):
            output[idx] = {
                "function": cur["function"],
                "value_inputs": [x for x in cur["value_inputs"]],
                "inputs": [],
            }
            next_idx = idx - 1
            for node in reversed(cur["inputs"]):
                output[idx]["inputs"].insert(0, next_idx)
                next_idx = helper(node, next_idx)
            return next_idx

        helper(program_tree, num_nodes - 1)
        return output

    def prefix_to_tree(self, program_prefix):
        program_prefix = [x for x in program_prefix]

        def helper():
            cur = program_prefix.pop(0)
            return {
                "function": cur["function"],
                "value_inputs": [x for x in cur["value_inputs"]],
                "inputs": [helper() for _ in range(self.get_num_inputs(cur))],
            }

        return helper()

    def prefix_to_list(self, program_prefix):
        return self.tree_to_list(self.prefix_to_tree(program_prefix))

    def list_to_postfix(self, program_list):
        return self.tree_to_postfix(self.list_to_tree(program_list))

    def postfix_to_tree(self, program_postfix):
        program_postfix = [x for x in program_postfix]

        def helper():
            cur = program_postfix.pop()
            return {
                "function": cur["function"],
                "value_inputs": [x for x in cur["value_inputs"]],
                "inputs": [helper() for _ in range(self, self.get_num_inputs(cur))][
                    ::-1
                ],
            }

        return helper()

    def postfix_to_list(self, program_postfix):
        return self.tree_to_list(self, self.postfix_to_tree(program_postfix))

    def get_num_inputs(self, f):
        f = function_to_str(f)
        return self._vocab["program_token_arity"][f]


def function_to_str(f):
    value_str = ""
    if f["value_inputs"]:
        value_str = "[%s]" % ",".join(f["value_inputs"])
    return "%s%s" % (f["function"], value_str)


def str_to_function(s):
    if "[" not in s:
        return {
            "function": s,
            "value_inputs": [],
        }
    name, value_str = s.replace("]", "").split("[")
    return {
        "function": name,
        "value_inputs": value_str.split(","),
    }


def list_to_str(program_list):
    return " ".join(function_to_str(f) for f in program_list)
