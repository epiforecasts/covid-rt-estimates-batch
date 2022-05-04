import argparse
import logging

from definitions.date_standards import DAY_OF_MONTH, DAY_OF_WEEK
from definitions.schedule import SCHEDULE
from run_covid_r_batch import run

LOGGER = logging.getLogger("covid-r-batch")


def main(args):

    production = args.production
    flags = args.flags
    datasets_to_run = []

    for item in SCHEDULE:
        if DAY_OF_MONTH in item.frequency or DAY_OF_WEEK in item.frequency:
            datasets_to_run.append(item)

    run(datasets_to_run, production, flags)


def setup():
    parser = argparse.ArgumentParser("Batch Scheduler")

    parser.add_argument("--flags", type=str, default="w",
                        help="additional flags to pass to the run script. e.g. 'fs' = -f -s. "
                             "Default value is w")
    parser.add_argument("--production", "-p", action="store_true",
                        default=False,
                        help="Runs in production mode. Dataset will be published,"
                             "runtimes.csv and status.csv will be commited to the repo")
    # process arguments
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main(setup())
