# Automated Errorlog Analyzer for Reference Clock

Automated Errorlog analzer is a multi threaded python script based tool which takes error log text file as input and parses it,
based on certain xml rules written by the user deduces the meaning of the content captured in the error log, and it also does a
root cause analysis to find the exact problem based within no-time.

## Requirements

The following are the python packages required for the script to run.

* [re](https://docs.python.org/3/library/re.html) - For regex support
* [threading](https://docs.python.org/3/library/threading.html) - For threading support
* [sys](https://docs.python.org/2/library/sys.html) - For the system calls support
* [untangle](https://untangle.readthedocs.io/en/latest/) - For xml Support
* [argparse](https://docs.python.org/2/howto/argparse.html) - For arguments and help
* [datetime](https://docs.python.org/2/library/datetime.html) - For manipulating dates and times
* [time](https://docs.python.org/2/library/time.html) - For time related functions support

## Usage

The following all the options supported by the tool.

``` ascii
errl_parser.py [-h] [--ruleHelp | --keyList | --errlEducation | --elog ELOG_PATH]
```

arguments:

```ascii
  -h, --help        show this help message and exit
  --ruleHelp        to print the help message on how to add custom rule
  --keyList         to print list of keys available in the oscc error log
  --errlEducation   to print the description of each keys available in the
                    oscc error log
  --elog ELOG_PATH  path to the error log file to be analyzed
```

## Contact

Manojkiran Eda - [@manojkiraneda](https://github.com/manojkiraneda)
Rajees R - [@rajees](https://github.com/rajez133)
