"""Build regressions that do not require compiled Essentia or audio fixtures."""

import ast
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_function(path, name, namespace):
    tree = ast.parse((ROOT / path).read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[name]


class BuildEntrypointTests(unittest.TestCase):
    def test_documentation_command_failure_is_fatal(self):
        commands = []

        def system(command):
            commands.append(command)
            return 256 if "doc/build_sphinx_doc.sh" in command else 0

        def fatal(message):
            raise RuntimeError(message)

        doc = load_function("wscript", "doc", {"os": SimpleNamespace(system=system, path=os.path), "sys": sys})
        with self.assertRaisesRegex(RuntimeError, "Failed to build documentation"):
            doc(SimpleNamespace(fatal=fatal))
        self.assertTrue(any("doc/build_sphinx_doc.sh" in command for command in commands))

    def test_source_links_use_the_build_commit_without_release_tags(self):
        commit = "1" * 40
        repo = SimpleNamespace(head=SimpleNamespace(commit=SimpleNamespace(hexsha=commit)))
        source_links = load_function("doc/sphinxdoc/generate_reference.py", "source_links", {
            "git": SimpleNamespace(Repo=lambda **kwargs: repo),
            "algo_path_dict": {"Test": Path("src/algorithms/test.cpp")},
        })
        self.assertEqual(source_links({"name": "Test"}), [
            f"https://github.com/MTG/essentia/blob/{commit}/src/algorithms/test.cpp",
            f"https://github.com/MTG/essentia/blob/{commit}/src/algorithms/test.h",
        ])


if __name__ == "__main__":
    unittest.main()
