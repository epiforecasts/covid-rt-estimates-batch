import argparse
import logging

from definitions.processable_entities import Dataset, Derivative
from run_covid_r_batch import run

LOGGER = logging.getLogger("covid-r-batch")


def main(args):
    datasets_to_run = []
    if args.collated:
        ds = Derivative(name=args.name, data_dir=args.data_dir, dependencies=[])
    else:
        ds = Dataset(name=args.name, data_dir=args.data_dir)
        if args.timeout:
            ds.timeout = args.timeout
    if args.wallclock_max_time:
        ds.max_wall_clock_minutes = args.wallclock_max_time
    datasets_to_run.append(ds)

    run(datasets_to_run, args.production, args.flags)


def setup():
    parser = argparse.ArgumentParser("Single Scheduler")
    parser.add_argument("--name", type=str, help="name for the dataset / collated derivative", required=True)
    parser.add_argument("-c", "--collated", action="store_true",
                        help="bool If True will treat the name as a collated derivative rather "
                             "than a dataset")
    parser.add_argument("-w", "--wallclock_max_time", type=int, default=300,
                        help="specify the wallclock kill time in minutes")
    parser.add_argument("-t", "--timeout", type=int, default=7200,
                        help="stan thread maximum execution time in seconds")
    parser.add_argument("--flags", type=str, default="w",
                        help="additional flags to pass to the run script. e.g. 'fs' = -f -s. "
                             "Default value is w")
    parser.add_argument("--production", "-p", action="store_true",
                        help="Runs in production mode. Dataset will be published,"
                             "runtimes.csv and status.csv will be commited to the repo")
    parser.add_argument("--data_dir", type=str,
                        help="Directory where results weill be stored", required=True)
    # process arguments
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main(setup())
