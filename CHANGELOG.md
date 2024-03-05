# Change Log

## 0.5.0

* make compatible with all Python versions from 3.8 through 3.12


## 0.4.0

* add parent to CovNode class
* ... with it, also add `root`
* make `coverage` and line number properties (tree should seldomly be too deep)
* remove `CovNode.follow_path`, simplify iterator to just yield nodes
* but add `path` property to node
* let path always start at root
* add `depth` to node
* separate Path and PathLike
* print total line and divider lines

## 0.3.0

* dynamically generate string for missed lines (ensures consistency)
* generate string for missing lines for modules
* restructure code folder tree
* move tree iteration function into node class
* rename threshold to descend
* check lines for consistency
* include cmdline in module
* bug fix: do not allow inserting into file node - even if done by path
* add ANSI escape sequence free printing
* add printing to file instead of stdout


## 0.2.0

* entire redesign of node class
* align coverage calculation with skipped lines with `coverage`
* option to show missing lines for cmd line tool
