# Introduction

**pydicomext** provides additional functionality to the [pydicom](https://pydicom.github.io/pydicom/dev) Python package which allows reading and saving DICOM files. This module extends *pydicom* to loading entire directories of DICOM files and organizing the data in terms of patients, studies and series to allow for easy traversal and identification of scans. In addition, *pydicomext* contains functions to manipulate series, merge two series together and even combine series into a Numpy volume is provided.

As of now, I do not feel comfortable releasing this project on PyPi yet because it is an early beta stage and I'm worried there are a bugs in the code. This project is used in multiple projects of mine and I did not want to have separate copies of the repository in case changes are made. **If you like this project and want to see it on PyPi, contact me somehow and let me know!***

**If you find this project to be useful in any way, then please let me know via a GitHub issue, email or however! This will motivate me to finish it and make it a PyPi library! Feedback is always welcome**

# Installation

# Cloning Repository (for projects without Git)

Cloning the repository can be done with the following commands in a Bash or Git Bash terminal with Git installed. In addition, Git GUIs such as GitHub Desktop, TortoiseGit, etc can be used to clone the repository as well.
```bash
git clone https://github.com/addisonElliott/pydicomext.git
```

Updating *pydicomext* can be done with the following commands within the pydicomext folder or once again by using a Git GUI.
```bash
git pull origin master
```

# Adding as Git Submodule (for projects with Git)

For projects that use Git for tracking changes in their source code, it is recommended to utilize *pydicomext* as a Git submodule. The primary advantage of this approach over cloning the repository is that it will not track any changes in the pydicomext folder.

XXX

If the project that uses pydicomext is tracked using Git, then you can create a Git submodule to this repository in your Git repository. This will prevent Git from tracking changes in the pydicomext and rather will treat it as it's own Git repository.

**Note:** For cloning your project with pydicomext as a Git submodule, there are a few extra steps that one must perform to clone the pydicomext module as well.
```bash
git submodule init
git submodule update
```

In addition you can do this all when cloning the repository by adding the *recurse-submodules* option.
```bash
git clone --recurse-submodules <REPO_LINK_HERE>
```

TODO: Finish me!
