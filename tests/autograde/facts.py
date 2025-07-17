"""Ground truth about the student's fork and clones. Read-only: never changes anything and never uses the network."""
from __future__ import annotations

import os
import re
import subprocess
from typing import List, NamedTuple, Optional, Set, Tuple

STAFF_SUBJECT = "chore: add lab assignment and grader"
UPDATE_SUBJECT = "docs: add contributing guide"  # the one commit the instructor publishes to the course repository
UPDATE_FILE = "CONTRIBUTING.md"
LIDAR_BRANCH = "feature/lidar-driver"
CONTRIB_FILE = "CONTRIBUTORS.md"
COURSE_SLUG = "qbit-glitch/26ra2308-gitlab-10-rover-fork-lab"  # lower case; the course repository students fork
COURSE_REPO = "26ra2308-gitlab-10-rover-fork-lab"
EXPLORE, SHALLOW, SINGLE = "rover-explore", "rover-shallow", "rover-single"  # the sibling clones of Tasks 1 and 2
GIT_TIMEOUT = 60
SLUG_RE = re.compile(r"github\.com[:/]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")


class GitError(RuntimeError):
    """Raised when the repository is not set up the way the grader expects."""


class Commit(NamedTuple):
    """A commit with the facts the grader needs."""

    sha: str
    author: str
    email: str
    subject: str
    parents: List[str]


def slug_of(url: str) -> str:
    """'owner/repo' (lower case) of a GitHub address in any of its forms ('' if it is not a GitHub address)."""
    match = SLUG_RE.search(url.strip())
    return f"{match.group(1)}/{match.group(2)}".lower() if match else ""


def run_git_rc(repo: str, *args: str) -> Tuple[int, str]:
    """Run git in 'repo' and return (exit code, stdout); a git call that hangs is stopped and reported as 124."""
    env = dict(os.environ, LC_ALL="C", GIT_PAGER="cat", GIT_TERMINAL_PROMPT="0")
    try:
        proc = subprocess.run(["git", *args], cwd=repo, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, encoding="utf-8", errors="replace", timeout=GIT_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return 124, ""
    return proc.returncode, proc.stdout


def run_git(repo: str, *args: str) -> str:
    """Run git in 'repo' and return stdout ('' on failure)."""
    return run_git_rc(repo, *args)[1]


def _commit(line: str) -> Optional[Commit]:
    parts = line.rstrip("\n").split("\x1f")
    return Commit(parts[0], parts[1], parts[2], parts[3], parts[4].split()) if len(parts) == 5 else None


FORMAT = "--format=%H%x1f%an%x1f%ae%x1f%s%x1f%P"


class Facts:
    """Everything the grader needs to know about the fork (and the clones next to it)."""

    def __init__(self, repo: str) -> None:
        self.repo = os.path.abspath(repo)
        if run_git_rc(self.repo, "rev-parse", "--verify", "-q", "refs/heads/main^{commit}")[0] != 0:
            raise GitError("branch main not found. Run the grader inside your clone of YOUR FORK (my-fork).")
        log = [c for c in map(_commit, run_git(self.repo, "log", "refs/heads/main", FORMAT).splitlines()) if c]
        staff = [c for c in log if c.subject == STAFF_SUBJECT]
        if not staff:
            raise GitError(f"the starting commit '{STAFF_SUBJECT}' is not in the history of main. "
                           "Run the grader inside your clone of your fork (made with 'git clone').")
        self.base: str = staff[-1].sha
        self.published: List[Commit] = [c for c in map(_commit, run_git(self.repo, "log", self.base, FORMAT).splitlines()) if c]

    # -- the starting history ------------------------------------------------------------
    def published_emails(self) -> Set[str]:
        """E-mail addresses of the people who wrote the starting history."""
        return {c.email.lower() for c in self.published}

    def published_names(self) -> Set[str]:
        """Names of the people who wrote the starting history."""
        return {c.author.lower() for c in self.published}

    # -- configuration, refs and objects ----------------------------------------------------
    def config_value(self, key: str) -> str:
        """Value of a repository-local config key ('' if unset)."""
        return run_git(self.repo, "config", "--local", "--get", key).strip()

    def effective_config(self, key: str) -> str:
        """Value of a config key as Git uses it in this repository, local or global ('' if unset)."""
        return run_git(self.repo, "config", "--get", key).strip()

    def remote_url(self, name: str) -> str:
        """The address stored for remote 'name' in this repository's own config ('' if there is none)."""
        return self.config_value(f"remote.{name}.url")

    def remote_names(self) -> List[str]:
        """The names of the remotes of this repository."""
        return run_git(self.repo, "remote").split()

    def branch_config(self, branch: str) -> Tuple[str, str]:
        """(remote, merge ref) a local branch is set up to track ('' for unset values)."""
        return self.config_value(f"branch.{branch}.remote"), self.config_value(f"branch.{branch}.merge")

    def rev(self, ref: str) -> str:
        """Full SHA of 'ref' ('' if it does not name a commit)."""
        return run_git(self.repo, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}").strip()

    def commit_exists(self, token: str) -> bool:
        """True if 'token' names a commit object in this repository."""
        return run_git_rc(self.repo, "cat-file", "-e", f"{token}^{{commit}}")[0] == 0

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """True if commit 'ancestor' is 'descendant' itself or part of its history."""
        return bool(ancestor) and bool(descendant) \
            and run_git_rc(self.repo, "merge-base", "--is-ancestor", ancestor, descendant)[0] == 0

    def file_at(self, ref: str, path: str) -> Optional[str]:
        """Content of 'path' at 'ref' (None if absent)."""
        code, out = run_git_rc(self.repo, "show", f"{ref}:{path}")
        return out if code == 0 else None

    def reflog(self, ref: str) -> List[str]:
        """Reflog messages of 'ref', newest first (empty if there is no reflog)."""
        return run_git(self.repo, "log", "-g", "--format=%gs", ref, "--").splitlines()

    def head_reflog(self) -> List[str]:
        """HEAD reflog messages, newest first."""
        return self.reflog("HEAD")

    def commit(self, ref: str) -> Optional[Commit]:
        """The commit 'ref' names (None if it names nothing)."""
        sha = self.rev(ref)
        return _commit(run_git(self.repo, "show", "-s", FORMAT, sha)) if sha else None

    def commits(self, spec: str) -> List[Commit]:
        """The commits in the range 'spec' (for example 'main..add-asha'), newest first."""
        code, out = run_git_rc(self.repo, "log", spec, FORMAT, "--")
        return [c for c in map(_commit, out.splitlines()) if c] if code == 0 else []

    def merges_in(self, spec: str) -> int:
        """Number of merge commits in the range 'spec' (-1 when the range is unknown)."""
        code, out = run_git_rc(self.repo, "rev-list", "--count", "--merges", spec, "--")
        return int(out) if code == 0 and out.strip().isdigit() else -1

    def main_tip(self) -> str:
        """Full SHA of the local branch main."""
        return self.rev("refs/heads/main")

    def clone_tip(self) -> str:
        """The commit main pointed at when the clone was made (the oldest line of main's reflog)."""
        lines = run_git(self.repo, "log", "-g", "--format=%H", "refs/heads/main", "--").split()
        return lines[-1] if lines else ""

    def update_commit(self) -> str:
        """SHA of the commit the instructor published ('docs: add contributing guide'), if this repo knows it."""
        for ref in ("refs/remotes/upstream/main", "refs/heads/main", "refs/remotes/origin/main"):
            for commit in self.commits(f"{self.base}..{ref}"):
                if commit.subject == UPDATE_SUBJECT:
                    return commit.sha
        return ""

    def contribution_branches(self) -> List[str]:
        """Local branches whose name starts with 'add-'."""
        names = run_git(self.repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/").split()
        return [n for n in names if n.startswith("add-")]

    def working_tree_clean(self) -> bool:
        """True when 'git status --porcelain' prints nothing and no merge or rebase is in progress."""
        clean = run_git(self.repo, "status", "--porcelain").strip() == ""
        merging = run_git_rc(self.repo, "rev-parse", "-q", "--verify", "MERGE_HEAD")[0] == 0
        return clean and not merging

    # -- the clones next to the fork (Tasks 1 and 2) ----------------------------------------
    def sibling(self, name: str) -> str:
        """Path of the clone 'name' next to the fork ('' when it is not there or not a repository)."""
        path = os.path.join(os.path.dirname(self.repo), name)
        return path if os.path.isdir(path) and run_git_rc(path, "rev-parse", "--git-dir")[0] == 0 else ""

    def sibling_git(self, name: str, *args: str) -> Tuple[int, str]:
        """Run git in the clone 'name' next to the fork ((127, '') when the clone is not there)."""
        path = self.sibling(name)
        return run_git_rc(path, *args) if path else (127, "")
