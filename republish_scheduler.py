import argparse
import logging

from definitions.processable_entities import Publication
from run_covid_r_batch import run

LOGGER = logging.getLogger("covid-r-batch")


def main(args):
    datasets_to_run = []
    ds = Publication(name=args.name, is_derivative=args.collated)
    datasets_to_run.append(ds)

    run(datasets_to_run, args)


def setup():
    parser = argparse.ArgumentParser("Single Scheduler")
    parser.add_argument("name", type=str, help="name for the dataset / collated derivative")
    parser.add_argument("-c", "--collated", action="store_true",
                        help="bool If True will treat the name as a collated derivative rather "
                             "than a dataset")
    parser.add_argument("--flags", type=str, default="w",
                        help="additional flags to pass to the run script. e.g. 'fs' = -f -s. "
                             "Default value is w")
    parser.add_argument("--production", "-p", action="store_true",
                        help="Runs in production mode. Dataset will be published,"
                             "runtimes.csv and status.csv will be commited to the repo")
    # process arguments
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main(setup())
