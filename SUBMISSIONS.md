# Submitting Your Work

Repository: `applied-ai-engineering-labs-2026`

Every task is submitted the same way: your own branch, your own folder, a pull request into `research`. The team lead reviews and merges.

## The rules

- **One branch per task**, created from the latest `research`, named `week<N>_<firstname>` in lowercase (for example `week4_<firstname>`).
- **One folder per task**, `week<N>/<firstname>/`. Add files only inside it, so your pull request can't collide with anyone else's.
- **Never push directly to `research` or `main`.** `main` is the reference copy and `research` is where merged work lives.
- **Never edit shared files** (the lead's code, other fellows' folders). If you need to change code, make a copy inside your own folder.
- **Submit by the deadline in the task brief.**

## Steps

### First time only:

```
git clone https://github.com/<org>/applied-ai-engineering-labs-2026.git
cd applied-ai-engineering-labs-2026
```

### For every task:

```
git checkout research
git pull origin research                 # always start from the latest
git checkout -b week<N>_<firstname>
```

### Create your folder and add your files

Inside the repository, create the folder `week<N>/<firstname>/` and put your files there.

- If you worked locally, save your files in that folder.
- If you worked in the cloud (for example Colab), download your files and copy them into that folder.

### Commit and push

```
git add week<N>/<firstname>/
git commit -m "Add week <N> <short description>"
git push origin week<N>_<firstname>
```

Then on GitHub, click **Compare & pull request** and set:

- **Base branch:** `research` (not `main`)
- **Compare branch:** `week<N>_<firstname>`
- **Title:** `Week <N>: <firstname> - <what you're submitting>`

## Folder layout

```
week<N>/<firstname>/
├── <the files named in the task brief>
└── ...
```

Use the file names the brief gives, exactly, so reviewers can find things quickly. If the task brief asks for a code change, make it in a copy inside your folder, one change per commit with a clear message, and keep your original results files.

## Revising after feedback

Commit and push to the **same branch**. The pull request updates automatically, so don't open a new one.

## After your pull request is merged

Delete your branch. Before the next task, pull the latest `research` and create a new branch. Don't reuse the old one.
