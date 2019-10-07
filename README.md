# DFS Frontend Migration

This script facilitates/automates the migration of DFS forms from DFS_FRONTEND to DFS_DIGITAL_FORMS_FRONTEND.




## Setup

To check whether you have `Python 3` installed:
```
which python3
``` 
or 
```
python3 --version
```

If not installed, install it: 
```
brew install python3
```
Then  you need to install `pip` or `pip3`
```
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```
Make sure `pip3` is installed: ```which pip3```


### Required Packages

Install the following packages using the command: `pip3 install <package name>`
- pyhocon
- ntpath
- nltk
- bs4

# How to run

In order to migrate a form from DFS_FRONTEND to DFS_DIGITAL_FORMS_FRONTEND follow these steps:

1. Find the the config for the form in `/dfs-frontend/conf/form-catalogue.conf`
2. Replace the content of `migrationConfig.conf` file with the config from step 1
3. Run the script in the terminal with: `Python3 migrate.py <formId>`
4. Read carefully through the logged messages (especially warnings) to make sure all is done as you expect
5. Make sure you can bring up the form on DFS_DIGITAL_FORMS_FRONTEND
6. Compare the form on DFS_FRONTEND to DFS_DIGITAL_FORMS_FRONTEND. When comparing note the followings:

    - the config file is generated properly and no form-specific configuration is missing
    - (if available) the guide pages are identical
    - (if available) the Welsh translation of guide pages are identical
    - the acknowledge pages are identical (except common differences between the 2 frontends)
    - (if available) the Welsh translation of acknowledge pages are identical
    - Run unit tests to confirm test updates were successful