# Git Lab Assignment: Kestrel-1 Rover, Join the Project

**Course:** 26RA2308 Git for Software Development and Collaboration
**Builds on:** Experiments 1 to 9. **Based on:** Experiment 10 (Cloning and Forking Repositories)
**Time allowed:** 1 hour. **Marks:** 100

---

## The story

The Kestrel-1 rover team has put its firmware on GitHub and invites outsiders to contribute. You are a new
contributor, and you are **not** a member of the team: you may read the project, but you may not write to it. This is
the situation every open-source contributor starts in, and the answer is always the same four moves:

1. **Look** at the project: `git clone`.
2. **Fork** it: your own copy on GitHub, which you may write to.
3. **Keep your fork up to date** with the original project, the *upstream*: `git fetch` and `git merge`.
4. **Work on a branch** of your fork and publish it.

In the next hour you clone the project over HTTPS and look at what you got (`git clone`, `git remote`, `git branch -a`),
make a shallow and a single-branch clone and see what they leave out (`--depth`, `--single-branch`), fork the project on
GitHub, add the original as `upstream`, bring your fork up to date, and push a branch that adds your name to the list
of contributors, ready for the pull request of Experiment 11. Along the way you reuse `git config` (Experiment 3),
`git commit` (Experiments 4 and 5), `git log` (Experiment 6), branches (Experiment 7), the `A..B` ranges of
Experiment 8, `git push -u` and `git branch -vv` (Experiment 9) and the terminal skills of Experiments 1 and 2.

## What you need

`git`, `python3` and a free **GitHub account**. Tasks 3 to 5 push to **your own fork** over SSH, so Git must know who you
are and GitHub must know your computer's SSH key. Check with `ssh -T git@github.com`: if it answers
`Hi <your-username>! You've successfully authenticated, but GitHub does not provide shell access.`, you are ready. If not,
do the next section **before the lab** (about 10 minutes, once). If your terminal does not print English messages, run
`export LC_ALL=C` first, because the grader reads what Git prints. If a long output opens in a pager (a screen with `:` or
`(END)` at the bottom), press `q` to leave it.

## Before the lab: connect Git to your GitHub account (once)

You did this in Experiment 3. If `ssh -T git@github.com` already greets you by name, skip this whole section. The document
`connect_git_and_github.docx` has the same steps with more explanation. Use **Git Bash** on Windows, Terminal on macOS.

**A. Tell Git who you are.** Use your own real name and the email address of your GitHub account (github.com, your picture,
Settings, Emails). The third line makes new repositories start on `main`.

```bash
git config --global user.name "Your Full Name"
git config --global user.email "your-email@example.com"
git config --global init.defaultBranch main
```

Read the values back; each command prints one value (your name, your email, `main`):

```bash
git config --global user.name
git config --global user.email
git config --global init.defaultBranch
```

**B. Make an SSH key.** First check that you do not already have one:

```bash
ls ~/.ssh/id_ed25519.pub
```

If it prints a path, you already have a key: do **not** make another one, and go to C. If it says
`No such file or directory`, make the key (use your own email). Answer the three questions with `Enter`: the place of the key,
and no passphrase, twice. (On a computer that other people use, type a passphrase instead and see the last paragraph of D.)

```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
```

It ends with `Your public key has been saved in .../.ssh/id_ed25519.pub`. The **private** key `~/.ssh/id_ed25519` never leaves
your computer: never send it or paste it anywhere.

**C. Give the public key to GitHub.** Print it: one line that starts with `ssh-ed25519` and ends with your email.

```bash
cat ~/.ssh/id_ed25519.pub
```

Select that line and copy it. In the browser: github.com, your picture (top right), **Settings**, **SSH and GPG keys**, the green
button **New SSH key**. **Title:** `Lab laptop`. **Key type:** *Authentication Key*. **Key:** paste the line. Click
**Add SSH key** (GitHub may ask for your password).

**D. Test it.**

```bash
ssh -T git@github.com
```

The first time, ssh asks you to check GitHub's computer:

```text
The authenticity of host 'github.com (...)' can't be established.
ED25519 key fingerprint is SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

If the fingerprint is exactly that one, type the whole word `yes` and press `Enter`. If it is different, type `no` and tell your
instructor. Then you must see your own user name:

```text
Hi YOUR-USERNAME! You've successfully authenticated, but GitHub does not provide shell access.
```

That sounds like an error but it is success. **If you set a passphrase**, ssh asks for it every time until you give the key to the
ssh-agent once per terminal window (type the passphrase when `ssh-add` asks):

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

**If it does not work:** `Permission denied (publickey)` means GitHub does not know the key it was offered: check that the whole
line of `id_ed25519.pub` is in the list under Settings, SSH and GPG keys, on the same account. `WARNING: UNPROTECTED PRIVATE KEY
FILE!` means the key is readable by others: run `chmod 600 ~/.ssh/id_ed25519`. `ssh: connect to host github.com port 22:
Connection refused` (or `timed out`) means your network blocks port 22: run the block below once, then test again.

```bash
mkdir -p ~/.ssh
cat >> ~/.ssh/config <<'EOF'
Host github.com
    Hostname ssh.github.com
    Port 443
    User git
EOF
chmod 600 ~/.ssh/config
```

## How to fork on github.com

Task 3 asks you to fork the project. Forking is a feature of GitHub, not a Git command.

1. Sign in to github.com and open `https://github.com/qbit-glitch/26RA2308-gitlab-10-rover-fork-lab`.
2. Click **Fork** (top right of the page).
3. On the page **Create a new fork**, leave the repository name as it is and leave **Copy the `main` branch only**
   ticked. Click **Create fork**.
4. GitHub shows your copy, `YOUR-USERNAME/26RA2308-gitlab-10-rover-fork-lab`, with the words *forked from
   qbit-glitch/26RA2308-gitlab-10-rover-fork-lab* under the name. Click the green **Code** button, choose **SSH**
   and copy the address that starts with `git@github.com:`.

## Rules

1. Work **only inside the folder `lab10`** that Task 1 creates. Tasks 1 and 2 happen in the clones made there, Tasks 3
   to 5 inside `my-fork`. Stay on `main`, except in Task 5, which makes a branch.
2. You cannot push to the course repository, so push **only to `origin`** of `my-fork`, your own fork. Never use
   `--force` (or `-f`) and never use `git reset`.
3. Type the commands yourself. The grader checks that your pasted output matches what is really in your clones (your
   commit numbers, your fork's address), so output copied from a classmate is detected.
4. Keep the folder names, the branch names and the commit messages exactly as written.

## How you hand in your work

1. In Task 1 you copy `outputs.template.txt` to a file named `outputs.txt` in `lab10`, next to the clones. It is
   outside every repository on purpose, so it can never be pushed by mistake.
2. After **each step** (numbered **1.1**, **1.2**, ...), paste what the terminal printed under the matching
   `--- N.M` line of `outputs.txt`, replacing `(paste output here)`. Do not edit or delete the
   `=== TASK` and `--- N.M` lines. Type your answers after the colon of the `ANSWER-n :` lines (the line just
   below each `# Qn` question). Any editor is fine for `outputs.txt`.
3. Fill in your name and registration number at the top of the file.
4. From Task 3 on, run the automatic grader whenever you want to see where you stand. Go into your fork first:

   ```bash
   cd my-fork
   python3 tests/grade.py
   ```

   It prints **PASS** or **FAIL** for every task, tells you exactly which check failed, and shows your score out
   of 100. You can fix a mistake and run it again as often as you like. The grader never uses the internet: it reads
   your fork and the clones next to it.
5. When you are done, show the final grader output to your instructor (it is also saved in `results.txt`, in `lab10`),
   and submit `outputs.txt` as instructed.

## Time plan

| Task | Time on the clock | Topic | Suggested time | Marks |
|---|---|---|---|---|
| 1 | 09:00 | Clone and inspect | 10 min | 20 |
| 2 | 09:10 | Shallow and single-branch clones | 8 min | 20 |
| 3 | 09:18 | Fork, clone and add upstream | 14 min | 25 |
| 4 | 09:32 | Sync the fork with upstream | 10 min | 20 |
| 5 | 09:42 | A contribution branch | 8 min | 15 |
| | | Buffer for running the grader and fixing mistakes | 10 min | |

**Skipped a task, or running behind?** You do not lose the rest of the lab. A **catch-up box** at the start of a later
task brings your folder to the state you need, in a few lines. If you skipped several tasks, run their boxes in order.
You lose only the marks of the task you skipped.

---

## Task 1: Clone and inspect (20 marks)

Make a work folder and clone the project into it. The project is public, so the HTTPS address needs no key.

```bash
mkdir lab10
cd lab10
git clone https://github.com/qbit-glitch/26RA2308-gitlab-10-rover-fork-lab.git rover-explore
```

* **1.1** Paste the output of `git clone`. `Cloning into 'rover-explore'...` is Git making the folder; the lines after
  it show the objects being downloaded.

```bash
cp rover-explore/submission/outputs.template.txt outputs.txt
cd rover-explore
git remote -v
```

* **1.2** Paste the output of `git remote -v`. A clone sets up `origin` for you, pointing at the address you cloned from.
  A clone can push only if you have write access to that address, and you have none here.

```bash
git branch -a
```

* **1.3** Paste the output. The `-a` shows local **and** remote-tracking branches. `remotes/origin/HEAD -> origin/main`
  says which branch the project calls its default. One remote branch is **not** on `main`: see which.

```bash
git log --oneline -5
cd ..
```

* **1.4** Paste the output of `git log --oneline -5` (the five newest commits). The `cd ..` brings you back to `lab10`.

## Task 2: Shallow and single-branch clones (20 marks)

A full clone downloads every commit of every branch. Often you need less, and the project keeps a long calibration
history, so the saving is visible. Stay in `lab10`.

*Needs:* the clone `rover-explore` of Task 1.

> **Catch-up box: only if you skipped Task 1.** Run these two lines, once, in `lab10`. They do what Task 1 does. If you
> did Task 1, do **not** run them. There is nothing to paste for them, and you lose only the marks of Task 1.
>
> ```bash
> git clone https://github.com/qbit-glitch/26RA2308-gitlab-10-rover-fork-lab.git rover-explore
> cp rover-explore/submission/outputs.template.txt outputs.txt
> ```

A **shallow** clone takes only the newest commit of the branch (`--depth 1`):

```bash
git clone --depth 1 https://github.com/qbit-glitch/26RA2308-gitlab-10-rover-fork-lab.git rover-shallow
```

* **2.1** Paste the output of `git clone`.

```bash
git -C rover-shallow log --oneline
```

* **2.2** Paste the output. The option `-C <folder>` runs Git as if you had gone into that folder. How many commits
  does the shallow clone have?

A **single-branch** clone takes the whole history, but only of the branch you name:

```bash
git clone --single-branch --branch main https://github.com/qbit-glitch/26RA2308-gitlab-10-rover-fork-lab.git rover-single
```

* **2.3** Paste the output of `git clone`.

```bash
git -C rover-single branch -a
```

* **2.4** Paste the output. Compare it with 1.3.

```bash
du -sh rover-explore/.git rover-shallow/.git rover-single/.git
```

* **2.5** Paste the output. `du -sh` prints the size of a folder in human-readable form. The `.git` folder is the
  repository itself. Which clone is smallest, and why?
* Then type your answer to `ANSWER-1` in the file (there is no pasted output for it): which branch of the course
  repository does `rover-explore` know, but `rover-single` does not?

## Task 3: Fork, clone and add upstream (25 marks)

Now make your own copy. In the browser, fork the project as described in the box "How to fork on github.com". Then,
in the terminal, in `lab10` (replace `YOUR-USERNAME` with your GitHub user name, and use your own real name and e-mail
below, not a placeholder and not one of the teammates'):

```bash
git clone git@github.com:YOUR-USERNAME/26RA2308-gitlab-10-rover-fork-lab.git my-fork
```

* **3.1** Paste the output of `git clone`. This time `origin` is **your fork**, and you may push to it.

```bash
cd my-fork
git config user.name "Your Full Name"
git config user.email "your.email@example.com"
git remote add upstream https://github.com/qbit-glitch/26RA2308-gitlab-10-rover-fork-lab.git
git remote -v
```

Do **not** use `--global` here. `upstream` is the conventional name for the original project: Git does not know it
exists until you add it, because a fork is a GitHub feature and a clone only remembers the address it came from.

* **3.2** Paste the output of `git remote -v`. Two remotes, listed twice each (fetch and push): `origin` is your
  fork, `upstream` is the original project.

```bash
git log --oneline --decorate -3
```

* **3.3** Paste the output. `--decorate` writes the branch names next to the commits they point at.
* Then type your answer to `ANSWER-2` in the file: which of your two remotes could you **not** push to?

## Task 4: Sync the fork with upstream (20 marks)

A fork does not follow the original project by itself. Before you start any new work you bring your fork up to date,
or your contribution will clash with newer work. **Your instructor will tell the room when the course repository has
a new commit** (it adds a file `CONTRIBUTING.md`). Wait for that announcement. If it has not come yet, do the task
anyway: Git then prints `Already up to date.`, which is correct, and the grader accepts it.

*Needs:* the fork of Task 3.

> **Catch-up box: only if you skipped Task 3.** In the browser, fork the project (the box "How to fork on
> github.com"). Then run these five lines, once, in `lab10`. They do what Task 3 does. If you did Task 3, do **not**
> run them. There is nothing to paste for them, and you lose only the marks of Task 3.
>
> ```bash
> git clone git@github.com:YOUR-USERNAME/26RA2308-gitlab-10-rover-fork-lab.git my-fork
> cd my-fork
> git config user.name "Your Full Name"
> git config user.email "your.email@example.com"
> git remote add upstream https://github.com/qbit-glitch/26RA2308-gitlab-10-rover-fork-lab.git
> ```

```bash
git fetch upstream
```

* **4.1** Paste the output. `git fetch` downloads what the original project has and stores it as `upstream/main` and
  its sibling branches. It does not touch your files or your `main`.

```bash
git log --oneline --decorate -3 upstream/main
```

* **4.2** Paste the output. Is `upstream/main` on the same commit as your `main`, or ahead of it?

```bash
git switch main
git merge upstream/main
```

* **4.3** Paste the output of `git merge`. When your `main` has nothing that `upstream/main` lacks, the merge only moves
  `main` forward: the word `Fast-forward`, and no new commit.

```bash
git push origin main
```

* **4.4** Paste the output. Your fork on GitHub is now level with the original project.

## Task 5: A contribution branch (15 marks)

Make your contribution on a **new branch**, never on `main`: `main` stays a clean copy of the original that you can
sync again, and the branch is what you will offer as a pull request in Experiment 11. Replace `yourfirstname` with your
first name in small letters, for example `add-asha`.

*Needs:* the synchronised `main` of Task 4.

> **Catch-up box: only if you skipped Task 4.** Run these four lines, once, in `my-fork`. They do what Task 4 does. If
> you did Task 4, do **not** run them. There is nothing to paste for them, and you lose only the marks of Task 4.
>
> ```bash
> git fetch upstream
> git switch main
> git merge upstream/main
> git push origin main
> ```

```bash
git switch -c add-yourfirstname
echo "- Your Full Name" >> CONTRIBUTORS.md
git commit -am "docs: add Your Full Name to contributors list"
```

Use the **same name** as in `git config user.name`. The `echo` adds one line to the end of the list. `-a` stages
every change to a tracked file and `-m` gives the message.

* **5.1** Paste the output of `git commit`.

```bash
git push -u origin add-yourfirstname
```

* **5.2** Paste the output. `-u` links your local branch to its twin on your fork.

```bash
git branch -vv
```

* **5.3** Paste the output. The word in square brackets is the branch that each of yours is tracking.

```bash
git log --oneline upstream/main..add-yourfirstname
```

* **5.4** Paste the output (the `A..B` range from Experiment 8): the commits your branch has that the original project
  does not.
* Then type your answer to `ANSWER-3` in the file: how many commits is that?

## Finish

You are inside `my-fork`. Run the grader:

```bash
python3 tests/grade.py
```

You want to see `PASS` for all five tasks and `TOTAL: 100/100`. Anything marked `FAIL` is listed with the reason; fix it
and run the grader again.

## Marks

| Task | Marks | How it is checked |
|---|---|---|
| 1 | 20 | the clone, the remote, the branch list and the log are pasted; `rover-explore` is really a full clone of the course repository |
| 2 | 20 | the two clones, the commit count, the branch list and the sizes are pasted; one answer; `rover-shallow` is really shallow and `rover-single` really fetches only `main` |
| 3 | 25 | the fork clone, the two remotes and the log are pasted; one answer; your identity, your own fork as `origin` and the course repository as `upstream` are real in `my-fork` |
| 4 | 20 | the fetch, the log, the merge and the push are pasted; the reflog shows a fetch, `main` contains `upstream/main`, and your fork on GitHub matches `main` |
| 5 | 15 | the commit, the push, `branch -vv` and the range are pasted; one answer; your branch holds exactly one commit that adds your name to `CONTRIBUTORS.md`, and `main` is untouched |

A task shows **PASS** only when every check in it passes, and you earn marks for each check that passes even if the
task as a whole fails.

## If something goes wrong

* **You skipped a task and a later one fails.** Run the catch-up box at the start of the task after the one you
  skipped (in order, if you skipped several), then carry on.
* **`Permission denied (publickey)` when you clone your fork.** GitHub does not know your SSH key. Do the section "Before the
  lab: connect Git to your GitHub account", parts B to D, and check with `ssh -T git@github.com` before you clone again.
* **`fatal: repository 'git@github.com:...' not found`.** The address is wrong, or you have not made the fork yet. Check
  `YOUR-USERNAME` and that the page `https://github.com/YOUR-USERNAME/26RA2308-gitlab-10-rover-fork-lab` exists.
* **`fatal: destination path 'my-fork' already exists and is not an empty directory`.** You ran the clone twice. Do not
  delete anything you need: if `my-fork` is a good clone, carry on from the next line.
* **`error: remote upstream already exists`.** You added it twice. Run `git remote -v` and carry on if it is right.
* **`fatal: 'upstream' does not appear to be a git repository`.** You did not add the remote. Run the
  `git remote add upstream ...` line of Task 3.
* **`merge: upstream/main - not something we can merge`.** You did not fetch yet: run `git fetch upstream` first.
* **`git merge` opens an editor, or says `CONFLICT`.** You have a commit of your own on `main` that `upstream/main` does
  not have, so Git has to make a real merge. Run `git merge --abort`, then `git status` and ask your instructor.
* **An editor opened and asked for a commit message.** You left out `-m "..."`. Save and exit (nano: `Ctrl+O`,
  `Enter`, `Ctrl+X`; vim: `Esc`, then `:wq` and `Enter`). Then fix the message with
  `git commit --amend -m "<the message from the step>"` (before you push).
* **`tests/grade.py` says it cannot find the starting commit, or cannot find `outputs.txt`.** You are not inside
  `my-fork`: `cd lab10/my-fork`, and `outputs.txt` must be in `lab10`.
* **Step 5.1 shows `[main ...]` instead of `[add-... ...]`.** You committed on `main`. Do not push. Ask your
  instructor: the grader will not give the marks that read the branch.
