# Packages Benchmarking

## Overall Functionality
The atopile project (https://github.com/atopile/atopile) has prebuilt designs called packages that enable rapid design reuse. Each package functions as a standalone design, capable of being compiled into build artifacts using atopile. More commonly, the packages are used as a design reuse block within a larger project, and can be added as a dependency to an atopile project using the `ato add atopile/<package-identifier>` command. Similar to code libraries, packages have a version number, and an atopile compatiblility version.

The goal of this code is to present unified, accurate data about the status of various packages. In order to verify the status of these packages, we will setup an array of environments using different versions of atopile as the test bed. Then we can run an ato build for each of the packages in each environment and we can extract information about the build such as success and speed.

## Environment Setup
The environment setup will be defined in a yaml file so it is sticky when edited. This environment yaml will contain information about atopile version and source to be installed. Create a virtual environment in ./benchmark_cache/<atopile-version-name>. THe virtual environment will be setup as follows:
1. Install atopile. There are 3 main sources of the atopile package we need to be able to install from.  
    1.1 A published version. Can be installed using `pip install atopile==<version>` command.  
    1.2 A github branch. The yaml will specify a github branch from the atopile repo. Clone the files into the environment folder, then use pip to install locally with `pip install ./<cloned-repo>`.  
    1.3 A local direcory. The yaml will specify local and a path. then use pip to install locally with `pip install <path-from-yaml>`.  

Use ato --version to verify the version of atopile that is installed and save this to the environment yaml for use in future reporting.

2. In each of the environment directories, clone the packages repo and checkout the main branch.

## Running Builds
Enable the virtual environment as source, the run an ato build for each project thats found in package/packages/. Each one of these directories is a package.  

Record the time elapsed from beginning the `ato build` command until the build completes as either a pass or fail for all build targets. Running `ato build` will automatically build all the build targets specified in the ato.yaml within the package. These builds generate entries into a database that has all the information about builds. Once the build starts, query the database once per second to get a status report on the build, and to check what build stage it is currently in. You can use the API to query the database and retrieve the information that is needed. In addition to recording the total time it took to build, we will also query the log database to extract how long each build step took so we can compare this information later.  

This build success/fail and timing information should be saved into a new file that is presented in the desired format for the frontend to consume.  

## GUI/Front End
### Configuration
The first UI element should be a configuration box, where you can configure which atopile versions you would like to include in your test matrix. You should be able to reorder the existing specified environements to be in any order you choose for plotting purposes later.  

We should have a list of selectable build commands, each of which will enable a different build results table. These build commands should be a regular `ato build`, `ato build --keep-picked-parts`, and default only `ato build -b default`. Each of these build commands will be the code command of which the result is being displayed in the table.  

There should be a button for start all tests, and a button for start all missing tests, which only runs tests that dont currently have a pass result.  

There should also be a dropdown selector for the number of parallel builds to allow at one time to try to limit concurrent builds from interfering with the speed result.  

### Build Results
Next UI element is a large table where each package is an expandable row. When collapsed the row should display the aggregate data for all build targets. When expanded, there should be a separate row per build target that shows the timing for each column.  

Each row will be a single atopile environment, i.e. a released version of atopile 0.12.4 and a branch of atopile 'stage/0.14.x'.  

Each data element will be a single box that either contains a time to complete build that is green to signify pass, a red failed box that you can click on to view the log, or a white N/A box if it has not been run yet.  

You should be able to sort this table by clicking on a filter/sort button on any of the columns, with clicking the name of the column acting as a toggle between sorting ascending and descending for that columm.  

Above each column there should be a few summary rows that indicate how many builds are passing out of the total number, the average build time across passing tests, and the normalized average build time across tests that are passing across ALL atopile environment versions. Its critical to not include pacakges that do not build on all selected atopile version in the normalized difference stat. Also summarize the average normalized difference for each atopile version across the available data.  