"""Detects pasted output that does not belong to the fork being graded."""
from __future__ import annotations

import re
from typing import List, Set

from .context import Ctx
from .facts import EXPLORE, SHALLOW, slug_of
from .tasks import TO_LINE_RE, own_slug, parse_remotes
from .textutil import line_shas

BRACKET_SHA_RE = re.compile(r"\[[^\]]*? ([0-9a-f]{7,40})\]")
RANGE_SHA_RE = re.compile(r"(?m)^\s+([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\s")
UPDATING_SHA_RE = re.compile(r"(?m)^Updating ([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\s*$")
FORK_STEPS = ("3.3", "4.2", "4.3", "4.4", "5.1", "5.2", "5.3", "5.4")  # produced inside the fork


def integrity_warnings(ctx: Ctx) -> List[str]:
    """Return human-readable warnings; an empty list means the pasted text matches this fork."""
    if not ctx.repo_mode:
        return []
    facts = ctx.facts
    warnings: List[str] = []
    live_slug = slug_of(facts.remote_url("origin"))
    pasted_slug = slug_of(parse_remotes(ctx.step("3.2")).get("origin", {}).get("fetch", ""))
    if live_slug and pasted_slug and live_slug != pasted_slug:
        warnings.append(f"the pasted 'git remote -v' shows origin as {pasted_slug} but this clone's origin is {live_slug}")
    mine = own_slug(ctx)
    wrong_target: Set[str] = set()
    foreign: Set[str] = set()
    for step_id in FORK_STEPS:
        text = ctx.step(step_id)
        for match in TO_LINE_RE.finditer(text):
            target = slug_of(match.group(1))
            if target and mine and target != mine:
                wrong_target.add(target)
        tokens = line_shas(text) + BRACKET_SHA_RE.findall(text)
        for pair in RANGE_SHA_RE.findall(text) + UPDATING_SHA_RE.findall(text):
            tokens += list(pair)
        for token in tokens:
            if not facts.commit_exists(token):
                foreign.add(token)
    # the commits printed in Tasks 1 and 2 must exist in the clone they came from (when that clone is still there)
    for step_id, clone in (("1.4", EXPLORE), ("2.2", SHALLOW)):
        if not facts.sibling(clone):
            continue
        for token in line_shas(ctx.step(step_id)):
            if facts.sibling_git(clone, "cat-file", "-e", f"{token}^{{commit}}")[0] != 0:
                foreign.add(token)
    if wrong_target:
        warnings.append("a pasted push or fetch names another repository than this fork: " + ", ".join(sorted(wrong_target)))
    if foreign:
        shown = ", ".join(sorted(foreign)[:6])
        warnings.append(f"{len(foreign)} commit SHA(s) in the pasted text do not exist in your clones "
                        f"(e.g. {shown}); the outputs were not produced here")
    return warnings

