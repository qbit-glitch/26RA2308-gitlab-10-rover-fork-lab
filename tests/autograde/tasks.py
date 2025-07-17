"""Graders for the five tasks of the Cloning and Forking lab."""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set

from .context import Ctx
from .facts import (
    COURSE_REPO, COURSE_SLUG, CONTRIB_FILE, EXPLORE, LIDAR_BRANCH, SHALLOW, SINGLE, STAFF_SUBJECT, UPDATE_FILE, run_git,
    slug_of,
)
from .framework import Task
from .textutil import BranchRow, get_answer, get_answer_int, header_field, oneline_entries, parse_branch_list, strip_decoration

PLACEHOLDER_NAMES = {"", "your full name", "your name"}
PLACEHOLDER_EMAILS = {"", "your.email@example.com"}
REMOTE_LINE_RE = re.compile(r"(?m)^(\S+)\s+(\S+)\s+\((fetch|push)\)\s*$")
PUSH_RANGE_RE = re.compile(r"(?m)^\s+([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\s+main\s+->\s+main\s*$")
UPDATING_RE = re.compile(r"(?m)^Updating ([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\s*$")
COMMIT_LINE_RE = re.compile(r"(?m)^\[(add-\S+) (?:\(root-commit\) )?([0-9a-f]{7,40})\] (.*)$")
TO_LINE_RE = re.compile(r"(?m)^To (\S+)\s*$")
DU_LINE_RE = re.compile(r"(?m)^\s*([0-9]+(?:\.[0-9]+)?)([BKMGT]?)\s+(\S+?)/?\s*$")
UNITS = {"": 1.0, "B": 1.0, "K": 1024.0, "M": 1024.0 ** 2, "G": 1024.0 ** 3, "T": 1024.0 ** 4}
CLONE_BRANCHES = {"main", "remotes/origin/HEAD", "remotes/origin/main", f"remotes/origin/{LIDAR_BRANCH}"}


def parse_remotes(text: str) -> Dict[str, Dict[str, str]]:
    """Read 'git remote -v' output into {remote name: {'fetch': url, 'push': url}}."""
    remotes: Dict[str, Dict[str, str]] = {}
    for name, url, kind in REMOTE_LINE_RE.findall(text):
        remotes.setdefault(name, {})[kind] = url
    return remotes


def parse_sizes(text: str) -> Dict[str, float]:
    """Read 'du -sh' output into {path: size in bytes}."""
    return {path: float(number) * UNITS[unit] for number, unit, path in DU_LINE_RE.findall(text)}


def branch_row(text: str, name: str) -> Optional[BranchRow]:
    """The row of 'git branch' output for one branch name (None if it is not listed)."""
    return next((r for r in parse_branch_list(text) if r.name == name), None)


def tracks(rest: str, upstream: str) -> bool:
    """True when the rest of a 'git branch -vv' row names this upstream in brackets, as in '[origin/main]'."""
    return re.search(r"\[" + re.escape(upstream) + r"[\]:]", rest) is not None


def to_slug(text: str) -> str:
    """'owner/repo' named by the first 'To <address>' line of a pasted push ('' if there is none)."""
    match = TO_LINE_RE.search(text)
    return slug_of(match.group(1)) if match else ""


def own_slug(ctx: Ctx) -> str:
    """'owner/repo' of the student's fork: from the clone's config when it can be read, else from the pasted 3.2."""
    live = slug_of(ctx.facts.remote_url("origin")) if ctx.repo_mode else ""
    if live and live != COURSE_SLUG:
        return live
    return slug_of(parse_remotes(ctx.step("3.2")).get("origin", {}).get("fetch", ""))


def names_of_student(ctx: Ctx) -> List[str]:
    """The names the contribution may carry: the Name line of the submission and the clone's user.name."""
    names = [header_field(ctx.text, "Name").strip()]
    if ctx.repo_mode:
        names.append(ctx.facts.effective_config("user.name"))
    return [n for n in names if n and n.lower() not in PLACEHOLDER_NAMES]


def _subjects(text: str) -> List[str]:
    return [strip_decoration(e.subject) for e in oneline_entries(text)]


def _answer_is(ctx: Ctx, number: int, *accepted: str) -> bool:
    return get_answer(ctx.text, number).strip("`'\" ").lower() in accepted


# -- Task 1 -----------------------------------------------------------------
def grade_task1(ctx: Ctx) -> Task:
    """Task 1: clone the course repository over HTTPS and look at it."""
    t = Task(1, "Clone and inspect", 20, ctx.repo_mode)
    f = ctx.facts
    s11 = ctx.step("1.1")
    t.check(3, "1.1 clone output: \"Cloning into 'rover-explore'...\"", lambda: "Cloning into 'rover-explore'" in s11)
    t.check(1, "1.1 clone output shows no error",
            lambda: "Cloning into" in s11 and re.search(r"(?i)\bfatal\b|\berror\b|empty repository", s11) is None)
    remotes = parse_remotes(ctx.step("1.2"))
    origin = remotes.get("origin", {})
    t.check(3, "1.2 remote -v: origin (fetch and push) is the course repository",
            lambda: slug_of(origin.get("fetch", "")) == COURSE_SLUG and slug_of(origin.get("push", "")) == COURSE_SLUG)
    t.check(1, "1.2 remote -v: the address is an https:// one (a clone of a public repository needs no key)",
            lambda: origin.get("fetch", "").startswith("https://") and origin.get("push", "").startswith("https://"))
    t.check(1, "1.2 remote -v lists exactly one remote, origin", lambda: set(remotes) == {"origin"})
    s13 = ctx.step("1.3")
    names = {r.name for r in parse_branch_list(s13)}
    main = branch_row(s13, "main")
    head = branch_row(s13, "remotes/origin/HEAD")
    t.check(1, "1.3 branch -a: main is the checked-out branch", lambda: main is not None and main.current)
    t.check(1, "1.3 branch -a: remotes/origin/HEAD -> origin/main", lambda: head is not None and "origin/main" in head.rest)
    t.check(1, "1.3 branch -a: remotes/origin/main is listed", lambda: "remotes/origin/main" in names)
    t.check(2, f"1.3 branch -a: remotes/origin/{LIDAR_BRANCH} is listed (the branch that is not on main)",
            lambda: f"remotes/origin/{LIDAR_BRANCH}" in names)
    t.check(1, "1.3 branch -a lists exactly the four lines a fresh clone has", lambda: names == CLONE_BRANCHES)
    s14 = ctx.step("1.4")
    t.check(2, "1.4 log -5: five commits", lambda: len(oneline_entries(s14)) == 5)
    t.check(2, "1.4 log -5: one of them is 'chore: add lab assignment and grader'", lambda: STAFF_SUBJECT in _subjects(s14))
    code, url = f.sibling_git(EXPLORE, "config", "--get", "remote.origin.url") if ctx.repo_mode else (1, "")
    t.check(1, "live repo: the folder rover-explore next to your fork is a full clone of the course repository",
            lambda: code == 0 and slug_of(url) == COURSE_SLUG
            and f.sibling_git(EXPLORE, "rev-parse", "--is-shallow-repository")[1].strip() == "false"
            and f.sibling_git(EXPLORE, "rev-parse", "--verify", "-q", f"refs/remotes/origin/{LIDAR_BRANCH}")[0] == 0,
            needs_repo=True, why=lambda: "expected a full clone named rover-explore in the same folder as my-fork")
    return t


# -- Task 2 -----------------------------------------------------------------
def grade_task2(ctx: Ctx) -> Task:
    """Task 2: a shallow clone and a single-branch clone, and what they leave out."""
    t = Task(2, "Shallow and single-branch clones", 20, ctx.repo_mode)
    f = ctx.facts
    t.check(2, "2.1 clone output: \"Cloning into 'rover-shallow'...\"", lambda: "Cloning into 'rover-shallow'" in ctx.step("2.1"))
    s22 = ctx.step("2.2")
    top = _subjects(ctx.step("1.4"))[:1]
    t.check(3, "2.2 log of the shallow clone: exactly one commit", lambda: len(oneline_entries(s22)) == 1)
    t.check(1, "2.2 that one commit is the newest commit seen in 1.4",
            lambda: bool(top) and _subjects(s22)[:1] == top)
    t.check(2, "2.3 clone output: \"Cloning into 'rover-single'...\"", lambda: "Cloning into 'rover-single'" in ctx.step("2.3"))
    s24 = ctx.step("2.4")
    names = {r.name for r in parse_branch_list(s24)}
    main = branch_row(s24, "main")
    t.check(3, "2.4 branch -a of the single-branch clone: main is checked out and remotes/origin/main is listed",
            lambda: main is not None and main.current and "remotes/origin/main" in names)
    t.check(1, f"2.4 the single-branch clone does not know {LIDAR_BRANCH}",
            lambda: bool(names) and names <= CLONE_BRANCHES - {f"remotes/origin/{LIDAR_BRANCH}"})
    sizes = parse_sizes(ctx.step("2.5"))
    keys = {name: f"{name}/.git" for name in (EXPLORE, SHALLOW, SINGLE)}
    t.check(1, "2.5 du lists the three .git folders", lambda: all(path in sizes for path in keys.values()))
    t.check(3, "2.5 the .git folder of the shallow clone is smaller than that of the full clone",
            lambda: sizes[keys[SHALLOW]] < sizes[keys[EXPLORE]])
    t.check(2, f"ANSWER-1 is {LIDAR_BRANCH} (the branch the single-branch clone does not have)",
            lambda: _answer_is(ctx, 1, LIDAR_BRANCH, "origin/" + LIDAR_BRANCH, "remotes/origin/" + LIDAR_BRANCH))
    t.check(1, "live repo: rover-shallow is really a shallow clone",
            lambda: f.sibling_git(SHALLOW, "rev-parse", "--is-shallow-repository")[1].strip() == "true", needs_repo=True,
            why=lambda: "expected a clone made with --depth 1 named rover-shallow next to my-fork")
    t.check(1, "live repo: rover-single is really a single-branch clone (it fetches only main)",
            lambda: f.sibling_git(SINGLE, "config", "--get", "remote.origin.fetch")[1].strip()
            == "+refs/heads/main:refs/remotes/origin/main", needs_repo=True,
            why=lambda: "expected a clone made with --single-branch --branch main named rover-single next to my-fork")
    return t


# -- Task 3 -----------------------------------------------------------------
def grade_task3(ctx: Ctx) -> Task:
    """Task 3: fork on GitHub, clone the fork and add the course repository as upstream."""
    t = Task(3, "Fork, clone and add upstream", 25, ctx.repo_mode)
    f = ctx.facts
    t.check(3, "3.1 clone output: \"Cloning into 'my-fork'...\"", lambda: "Cloning into 'my-fork'" in ctx.step("3.1"))
    remotes = parse_remotes(ctx.step("3.2"))
    origin, upstream = remotes.get("origin", {}), remotes.get("upstream", {})
    mine = slug_of(origin.get("fetch", ""))
    t.check(4, "3.2 remote -v: origin (fetch and push) is your own fork, not the course repository",
            lambda: bool(mine) and mine != COURSE_SLUG and slug_of(origin.get("push", "")) == mine)
    t.check(4, "3.2 remote -v: upstream (fetch and push) is the course repository",
            lambda: slug_of(upstream.get("fetch", "")) == COURSE_SLUG and slug_of(upstream.get("push", "")) == COURSE_SLUG)
    t.check(1, "3.2 remote -v lists exactly two remotes, origin and upstream", lambda: set(remotes) == {"origin", "upstream"})
    t.check(1, "3.2 your fork has the same repository name as the course repository (a fork keeps the name)",
            lambda: bool(mine) and mine.split("/")[1] == COURSE_REPO)
    s33 = ctx.step("3.3")
    entries = oneline_entries(s33)
    t.check(1, "3.3 log -3: three commits", lambda: len(entries) == 3)
    t.check(2, "3.3 log -3: the newest commit is HEAD -> main and origin/main",
            lambda: bool(entries) and "HEAD -> main" in entries[0].subject and "origin/main" in entries[0].subject)
    t.check(1, "3.3 log -3: one of them is 'chore: add lab assignment and grader'", lambda: STAFF_SUBJECT in _subjects(s33))
    t.check(2, "ANSWER-2 is upstream (the remote you have no right to push to)", lambda: _answer_is(ctx, 2, "upstream"))
    name, email = f.config_value("user.name"), f.config_value("user.email")
    t.check(2, "live repo: your identity is set in this clone (not a placeholder, not a teammate's)",
            lambda: name.lower() not in PLACEHOLDER_NAMES and "@" in email and email.lower() not in PLACEHOLDER_EMAILS
            and name.lower() not in f.published_names() and email.lower() not in f.published_emails(),
            needs_repo=True)
    url = f.remote_url("origin") if ctx.repo_mode else ""
    t.check(2, "live repo: origin is a GitHub address of your own (not the course repository) and matches the pasted one",
            lambda: bool(slug_of(url)) and slug_of(url) != COURSE_SLUG and (not mine or slug_of(url) == mine),
            needs_repo=True, why=lambda: "origin must be your own fork (made with git clone of YOUR repository)")
    t.check(2, "live repo: the remote upstream is the course repository",
            lambda: slug_of(f.remote_url("upstream")) == COURSE_SLUG, needs_repo=True,
            why=lambda: "add it with: git remote add upstream https://github.com/qbit-glitch/26RA2308-gitlab-10-rover-fork-lab.git")
    return t


# -- Task 4 -----------------------------------------------------------------
def grade_task4(ctx: Ctx) -> Task:
    """Task 4: bring the fork up to date from upstream (fetch, look, merge, push)."""
    t = Task(4, "Sync the fork with upstream", 20, ctx.repo_mode)
    f = ctx.facts
    mine = own_slug(ctx)
    s41 = ctx.step("4.1")
    t.check(1, "4.1 fetch output: 'From' the course repository",
            lambda: any(ln.startswith("From ") and slug_of(ln[5:]) == COURSE_SLUG for ln in s41.split("\n")))
    t.check(4, "4.1 fetch output: '* [new branch]  main -> upstream/main'",
            lambda: re.search(r"\* \[new branch\]\s+main\s+-> upstream/main", s41) is not None)
    s42 = ctx.step("4.2")
    entries = oneline_entries(s42)
    t.check(1, "4.2 log -3 upstream/main: three commits", lambda: len(entries) == 3)
    t.check(1, "4.2 log -3 upstream/main: the newest commit is upstream/main",
            lambda: bool(entries) and "upstream/main" in entries[0].subject)
    t.check(1, "4.2 log -3 upstream/main: one of them is 'chore: add lab assignment and grader'",
            lambda: STAFF_SUBJECT in _subjects(s42))
    # upstream is ahead of main exactly when the newest commit is not also HEAD -> main
    pending = bool(entries) and "HEAD -> main" not in entries[0].subject
    s43 = ctx.step("4.3")
    updating = UPDATING_RE.search(s43)
    if pending:
        merged = (updating is not None and "Fast-forward" in s43 and re.search(re.escape(UPDATE_FILE) + r" +\| +\d+ \++", s43)
                  is not None)
        what = f"4.3 merge output: 'Updating <old>..<new>', 'Fast-forward' and {UPDATE_FILE} added (upstream had a new commit)"
    else:
        merged = "Already up to date." in s43
        what = "4.3 merge output: 'Already up to date.' (4.2 shows upstream/main has nothing new)"
    t.check(3, what, lambda: merged)
    t.check(2, "4.3 merge output: no merge commit and no conflict",
            lambda: bool(s43.strip()) and re.search(r"Merge made by|CONFLICT|Automatic merge failed", s43) is None)
    s44 = ctx.step("4.4")
    pushed = PUSH_RANGE_RE.search(s44)
    if pending:
        t.check(3, "4.4 push output: '<old>..<new>  main -> main' (accepted)", lambda: pushed is not None and "! [rejected]" not in s44)
        t.check(1, "4.4 the push went to your own fork", lambda: bool(mine) and to_slug(s44) == mine)
    else:
        t.check(3, "4.4 push output: 'Everything up-to-date' (nothing new to send)", lambda: "Everything up-to-date" in s44)
        t.check(1, "4.4 the push did not fail",
                lambda: bool(s44.strip()) and "error:" not in s44 and "! [rejected]" not in s44)
    upstream_tip = f.rev("refs/remotes/upstream/main") if ctx.repo_mode else ""
    update = f.update_commit() if ctx.repo_mode else ""
    t.check(1, "live repo: the reflog of upstream/main records a fetch ('fetch upstream')",
            lambda: any(m.startswith("fetch") for m in f.reflog("refs/remotes/upstream/main")), needs_repo=True,
            why=lambda: "no 'git fetch upstream' was run in this clone")
    t.check(1, "live repo: main contains everything upstream/main has (the fork is up to date)",
            lambda: bool(upstream_tip) and f.is_ancestor(upstream_tip, f.main_tip())
            and (not update or f.is_ancestor(update, f.main_tip())), needs_repo=True,
            why=lambda: "main is behind upstream/main: git merge upstream/main")
    t.check(1, "live repo: origin/main is the same commit as main (the sync reached your fork on GitHub)",
            lambda: bool(upstream_tip) and f.rev("refs/remotes/origin/main") == f.main_tip() and bool(f.main_tip()),
            needs_repo=True,
            why=lambda: "git push origin main")
    return t


# -- Task 5 -----------------------------------------------------------------
def grade_task5(ctx: Ctx) -> Task:
    """Task 5: a contribution branch with one commit that adds your name, pushed to your fork."""
    t = Task(5, "A contribution branch", 15, ctx.repo_mode)
    f = ctx.facts
    names = names_of_student(ctx)
    wanted: Set[str] = {f"docs: add {n} to contributors list" for n in names}
    s51 = ctx.step("5.1")
    made = COMMIT_LINE_RE.search(s51)
    branch = made.group(1) if made else ""
    t.check(2, "5.1 commit output: '[add-<you> <sha>] docs: add <your name> to contributors list' on a branch whose name starts with add-",
            lambda: made is not None and made.group(3).strip() in wanted)
    t.check(1, "5.1 commit output: 1 file changed, 1 insertion(+)",
            lambda: re.search(r"\b1 file changed, 1 insertion\(\+\)", s51) is not None)
    s52 = ctx.step("5.2")
    esc = re.escape(branch)
    t.check(2, "5.2 push output: '* [new branch]  add-<you> -> add-<you>'",
            lambda: bool(branch) and re.search(r"\* \[new branch\]\s+" + esc + " -> " + esc, s52) is not None)
    t.check(2, "5.2 push output: branch 'add-<you>' set up to track 'origin/add-<you>' (this is what -u does)",
            lambda: bool(branch) and re.search(r"(?i)branch '" + esc + r"' set up to track (?:remote branch '" + esc
                                               + r"' from 'origin'|'origin/" + esc + "')", s52) is not None)
    s53 = ctx.step("5.3")
    mine_row, main_row = branch_row(s53, branch) if branch else None, branch_row(s53, "main")
    t.check(1, "5.3 branch -vv: the checked-out add-<you> branch tracks [origin/add-<you>]",
            lambda: mine_row is not None and mine_row.current and tracks(mine_row.rest, "origin/" + branch))
    t.check(1, "5.3 branch -vv: main tracks [origin/main]", lambda: main_row is not None and tracks(main_row.rest, "origin/main"))
    s54 = ctx.step("5.4")
    t.check(1, "5.4 log upstream/main..add-<you>: exactly one commit, your 'docs: add <your name> to contributors list'",
            lambda: len(oneline_entries(s54)) == 1 and _subjects(s54)[0] in wanted)
    t.check(1, "ANSWER-3 is 1 (commits your branch has that the course repository does not)",
            lambda: get_answer_int(ctx.text, 3) == "1")
    local = f.contribution_branches() if ctx.repo_mode else []
    tip = f.rev(f"refs/heads/{branch}") if ctx.repo_mode and branch else ""
    t.check(1, "live repo: the branch tracks origin/add-<you> and its tip is the same commit on GitHub",
            lambda: bool(tip) and f.branch_config(branch) == ("origin", f"refs/heads/{branch}")
            and f.rev(f"refs/remotes/origin/{branch}") == tip, needs_repo=True,
            why=lambda: f"branches starting with add-: {', '.join(local) or 'none'}; push with -u")
    commit = f.commit(tip) if tip else None

    def adds_only_my_name() -> bool:
        if commit is None or len(commit.parents) != 1 or not names:
            return False
        before, after = f.file_at(commit.parents[0], CONTRIB_FILE), f.file_at(commit.sha, CONTRIB_FILE)
        if before is None or after is None:
            return False
        lines = [ln.rstrip() for ln in after.splitlines()]
        new = [n for n in names if lines == [ln.rstrip() for ln in before.splitlines()] + [f"- {n}"]]
        files = [x for x in run_git(f.repo, "diff-tree", "--no-commit-id", "--name-only", "-r", commit.sha).split() if x]
        who = {n.lower() for n in names}
        return bool(new) and files == [CONTRIB_FILE] and commit.subject in wanted and commit.author.lower() in who \
            and "@" in commit.email and commit.email.lower() not in f.published_emails()
    t.check(2, "live repo: the tip commit is yours and adds exactly one line, '- <your name>', to CONTRIBUTORS.md (nothing else)",
            adds_only_my_name, needs_repo=True,
            why=lambda: "expected one commit that appends '- <your name>' to CONTRIBUTORS.md and changes no other file")
    t.check(1, "live repo: your commit sits straight on main (main..add-<you> is that one commit) and main has no commit of yours",
            lambda: commit is not None and f.commits(f"main..{branch}") == [commit] and commit.parents == [f.main_tip()]
            and not f.commits("refs/remotes/upstream/main..main"), needs_repo=True,
            why=lambda: "make the change on a new branch cut from an up-to-date main, never on main itself")
    return t

