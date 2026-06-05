"""A static, offline kubectl completer for prompt_toolkit.

Completion uses fixed tables of verbs, resource types, and flags — no calls are
made to a cluster, so it works offline and in tests. The structure is a small
nested grammar that is easy to extend to other CLIs (helm, docker) later.
"""

from __future__ import annotations

from collections.abc import Iterable

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

# Common kubectl verbs (subcommands).
VERBS: list[str] = [
    "get",
    "describe",
    "logs",
    "apply",
    "create",
    "delete",
    "edit",
    "exec",
    "explain",
    "expose",
    "scale",
    "rollout",
    "port-forward",
    "top",
    "config",
    "cluster-info",
    "cordon",
    "drain",
    "label",
    "annotate",
    "patch",
    "set",
    "run",
    "attach",
    "cp",
    "version",
]

# Common resource types (singular forms; kubectl also accepts plurals/short names).
RESOURCES: list[str] = [
    "pods",
    "pod",
    "deployments",
    "deployment",
    "services",
    "service",
    "svc",
    "nodes",
    "node",
    "namespaces",
    "namespace",
    "ns",
    "configmaps",
    "configmap",
    "secrets",
    "secret",
    "ingresses",
    "ingress",
    "replicasets",
    "replicaset",
    "statefulsets",
    "statefulset",
    "daemonsets",
    "daemonset",
    "jobs",
    "job",
    "cronjobs",
    "cronjob",
    "persistentvolumes",
    "pv",
    "persistentvolumeclaims",
    "pvc",
    "events",
    "endpoints",
    "serviceaccounts",
]

# Verbs that operate on a resource type as their next argument.
RESOURCE_VERBS: frozenset[str] = frozenset(
    {
        "get",
        "describe",
        "delete",
        "edit",
        "label",
        "annotate",
        "patch",
        "explain",
        "scale",
        "expose",
        "top",
    }
)

# Common flags.
FLAGS: list[str] = [
    "-n",
    "--namespace",
    "-o",
    "--output",
    "-A",
    "--all-namespaces",
    "-l",
    "--selector",
    "-w",
    "--watch",
    "-f",
    "--filename",
    "--context",
    "--kubeconfig",
    "-h",
    "--help",
]


def _matches(word: str, candidates: Iterable[str]) -> Iterable[str]:
    return [c for c in candidates if c.startswith(word)]


class KubectlCompleter(Completer):
    """Position-aware completion for ``kubectl`` command lines."""

    def get_completions(self, document: Document, complete_event):  # noqa: ANN001
        text = document.text_before_cursor
        stripped = text.lstrip()

        # Only engage for kubectl command lines.
        if not (stripped == "kubectl" or stripped.startswith("kubectl ")):
            return

        word = document.get_word_before_cursor(WORD=True)

        # Split into tokens; the last token is the partial word being typed
        # (empty when the cursor follows a space).
        tokens = stripped.split()
        ends_with_space = text.endswith((" ", "\t"))
        # Tokens excluding "kubectl" and excluding the partial word at the end.
        prior = tokens[1:] if ends_with_space else tokens[1:-1]

        candidates = self._candidates(prior, word)
        for c in _matches(word, candidates):
            yield Completion(c, start_position=-len(word))

    def _candidates(self, prior: list[str], word: str) -> list[str]:
        # Flags can appear anywhere once we're past the verb.
        if word.startswith("-"):
            return FLAGS

        non_flag = [t for t in prior if not t.startswith("-")]

        if not non_flag:
            # Right after "kubectl": complete a verb.
            return VERBS

        verb = non_flag[0]
        if verb in RESOURCE_VERBS and len(non_flag) == 1:
            # After a resource verb: complete a resource type.
            return RESOURCES

        # Past the resource type (e.g. a resource name): nothing static to offer.
        return []
