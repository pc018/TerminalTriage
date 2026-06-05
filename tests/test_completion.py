"""Tests for kubectl auto-completion.

Two layers are exercised:

* the **delegation** path, where the completer calls ``kubectl __complete`` — we
  inject a fake runner returning canned cobra output so tests stay offline;
* the **static fallback** path, used when kubectl is unavailable — forced here by
  injecting a runner that returns ``None``.
"""

from __future__ import annotations

from prompt_toolkit.document import Document

from terminal_triage.completion.kubectl import (
    KubectlCompleter,
    _parse_complete_output,
)


def _complete(text: str, runner=None, live: bool = False) -> list[str]:
    completer = KubectlCompleter(runner=runner, live=live)
    doc = Document(text, cursor_position=len(text))
    return [c.text for c in completer.get_completions(doc, None)]


# --- Delegation to ``kubectl __complete`` --------------------------------------


def _fake_runner(table: dict[tuple[str, ...], str]):
    """Build a runner that maps exact ``comp_args`` tuples to canned stdout."""

    def runner(args: list[str]) -> str | None:
        return table.get(tuple(args))

    return runner


def test_delegates_subcommands():
    runner = _fake_runner(
        {("",): "get\tDisplay resources\nevents\tList events\n:4\n"}
    )
    results = _complete("kubectl ", runner=runner, live=True)
    assert "get" in results
    assert "events" in results


def test_delegates_events_subcommand_prefix():
    # The original bug: `events` is a real subcommand and must complete.
    runner = _fake_runner({("ev",): "events\tList events\n:4\n"})
    results = _complete("kubectl ev", runner=runner, live=True)
    assert results == ["events"]


def test_delegates_dynamic_namespace_values():
    # `kubectl events -n <TAB>` completes real namespace names from the cluster.
    runner = _fake_runner(
        {("events", "-n", ""): "kube-system\nkube-public\ndefault\n:4\n"}
    )
    results = _complete("kubectl events -n ", runner=runner, live=True)
    assert "kube-system" in results
    assert "default" in results


def test_delegates_includes_crds():
    runner = _fake_runner(
        {("get", "no"): "nodes\nnodes.metrics.k8s.io\nnodefeatures.nfd.k8s-sigs.io\n:4\n"}
    )
    results = _complete("kubectl get no", runner=runner, live=True)
    assert "nodes" in results
    assert "nodes.metrics.k8s.io" in results


def test_live_failure_falls_back_to_static():
    # kubectl present but the call failed (runner returns None) -> static grammar.
    results = _complete("kubectl ", runner=lambda args: None, live=True)
    assert "get" in results  # served from the static fallback


def test_offline_default_never_calls_runner():
    # With live=False (the default), the runner must not be consulted at all.
    def boom(_args):
        raise AssertionError("runner should not be called when live=False")

    results = _complete("kubectl ", runner=boom)  # live defaults to False
    assert "get" in results


def test_parse_stops_at_directive_and_strips_descriptions():
    pairs = _parse_complete_output("get\tDisplay one\nevents\tList events\n:4\nignored\n")
    assert pairs == [("get", "Display one"), ("events", "List events")]


def test_no_completion_for_other_commands_with_runner():
    runner = _fake_runner({})  # never consulted for non-kubectl lines
    assert _complete("ls -la", runner=runner) == []
    assert _complete("helm install", runner=runner) == []


# --- Static fallback (kubectl unavailable) -------------------------------------

def _offline(_args):  # runner that signals "kubectl missing" -> static fallback
    return None


def test_fallback_verbs_after_kubectl():
    results = _complete("kubectl ", runner=_offline)
    assert "get" in results
    assert "describe" in results
    assert "events" in results  # now present in the static fallback too


def test_fallback_verb_prefix_filter():
    results = _complete("kubectl de", runner=_offline)
    assert "describe" in results
    assert "delete" in results
    assert "get" not in results


def test_fallback_resources_after_get():
    results = _complete("kubectl get ", runner=_offline)
    assert "pods" in results
    assert "deployments" in results
    assert "nodes" in results


def test_fallback_flags_after_dash():
    results = _complete("kubectl get pods -", runner=_offline)
    assert "-n" in results
    assert "--all-namespaces" in results


def test_fallback_no_completion_for_other_commands():
    assert _complete("ls -la", runner=_offline) == []
    assert _complete("helm install", runner=_offline) == []
