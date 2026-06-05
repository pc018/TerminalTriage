"""kubectl completion for prompt_toolkit.

The completer asks ``kubectl`` itself for suggestions via the hidden cobra
``__complete`` command (the same engine behind ``kubectl completion bash|zsh``).
That makes *every* subcommand, resource type — including cluster-specific CRDs —
and dynamic value (namespaces, pod names, contexts) complete correctly.

When ``kubectl`` is not on ``$PATH`` (or the call fails/times out), the completer
falls back to a small static grammar so it still does something useful offline.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Iterable

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

# How long to wait for ``kubectl __complete``. Dynamic value completion (e.g.
# namespace names) talks to the cluster, so cap it to keep the REPL responsive.
_COMPLETE_TIMEOUT_S = 2.0

# Type of the injectable runner: takes the args after "kubectl" (last item is the
# partial word, possibly "") and returns ``__complete`` stdout, or None on failure.
Runner = Callable[[list[str]], "str | None"]


def _run_kubectl_complete(args: list[str]) -> str | None:
    """Invoke ``kubectl __complete <args>`` and return its stdout, or None.

    Returns None when kubectl is missing, errors, or exceeds the timeout, so the
    caller can fall back to the static grammar.
    """
    if shutil.which("kubectl") is None:
        return None
    try:
        proc = subprocess.run(
            ["kubectl", "__complete", *args],
            capture_output=True,
            text=True,
            timeout=_COMPLETE_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _parse_complete_output(output: str) -> list[tuple[str, str]]:
    """Parse ``__complete`` stdout into ``(value, description)`` pairs.

    Cobra emits one ``value<TAB>description`` per line, terminated by a directive
    line beginning with ``:`` (which we stop at and discard).
    """
    pairs: list[tuple[str, str]] = []
    for line in output.splitlines():
        if line.startswith(":"):
            break
        if not line:
            continue
        value, _, description = line.partition("\t")
        if value:
            pairs.append((value, description.strip()))
    return pairs


# ---------------------------------------------------------------------------
# Static fallback grammar (used only when kubectl is unavailable / offline).
# ---------------------------------------------------------------------------

VERBS: list[str] = [
    "get",
    "describe",
    "logs",
    "events",
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
    "auth",
    "debug",
    "wait",
    "api-resources",
    "version",
]

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
    """Position-aware completion for ``kubectl`` command lines.

    By default the completer is fully offline, driven by a small static grammar.
    When ``live=True`` it instead delegates to ``kubectl __complete`` (see
    :func:`_run_kubectl_complete`) for authoritative, cluster-aware suggestions —
    this is opt-in because that call talks to the cluster. If the live call fails
    or times out it falls back to the static grammar.

    Pass ``runner`` to inject a fake in tests so they stay offline and deterministic.
    """

    def __init__(self, runner: Runner | None = None, *, live: bool = False) -> None:
        self._live = live
        self._runner: Runner = runner if runner is not None else _run_kubectl_complete

    def get_completions(self, document: Document, complete_event):  # noqa: ANN001
        text = document.text_before_cursor
        stripped = text.lstrip()

        # Only engage for kubectl command lines.
        if not (stripped == "kubectl" or stripped.startswith("kubectl ")):
            return

        word = document.get_word_before_cursor(WORD=True)

        tokens = stripped.split()
        ends_with_space = text.endswith((" ", "\t"))

        # Live mode: ask kubectl itself (talks to the cluster). Opt-in only.
        if self._live:
            # Args for ``kubectl __complete``: everything after "kubectl", with the
            # final element being the partial word being typed ("" after a space).
            comp_args = tokens[1:]
            if ends_with_space:
                comp_args = [*comp_args, ""]

            output = self._runner(comp_args)
            if output is not None:
                for value, description in _parse_complete_output(output):
                    yield Completion(
                        value,
                        start_position=-len(word),
                        display_meta=description or None,
                    )
                return
            # else: kubectl unavailable/failed -> fall through to static grammar.

        # Offline default (and live fallback): static grammar.
        prior = tokens[1:] if ends_with_space else tokens[1:-1]
        for c in _matches(word, self._static_candidates(prior, word)):
            yield Completion(c, start_position=-len(word))

    def _static_candidates(self, prior: list[str], word: str) -> list[str]:
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
