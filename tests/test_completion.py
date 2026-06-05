"""Tests for kubectl auto-completion."""

from __future__ import annotations

from prompt_toolkit.document import Document

from terminal_triage.completion.kubectl import KubectlCompleter


def _complete(text: str) -> list[str]:
    completer = KubectlCompleter()
    doc = Document(text, cursor_position=len(text))
    return [c.text for c in completer.get_completions(doc, None)]


def test_verbs_after_kubectl():
    results = _complete("kubectl ")
    assert "get" in results
    assert "describe" in results
    assert "logs" in results


def test_verb_prefix_filter():
    results = _complete("kubectl de")
    assert "describe" in results
    assert "delete" in results
    assert "get" not in results


def test_resources_after_get():
    results = _complete("kubectl get ")
    assert "pods" in results
    assert "deployments" in results
    assert "nodes" in results


def test_resource_prefix_filter():
    results = _complete("kubectl get po")
    assert "pods" in results
    assert "nodes" not in results


def test_flags_after_dash():
    results = _complete("kubectl get pods -")
    assert "-n" in results
    assert "--all-namespaces" in results


def test_no_completion_for_other_commands():
    assert _complete("ls -la") == []
    assert _complete("helm install") == []


def test_no_resources_for_non_resource_verb():
    # `logs` is not a resource verb, so no resource types are offered.
    results = _complete("kubectl logs ")
    assert "pods" not in results
