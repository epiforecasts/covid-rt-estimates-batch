import argparse
import logging

from definitions.processable_entities import Publication, ReSummarise
from run_covid_r_batch import run

LOGGER = logging.getLogger("covid-r-batch")

PUBLISH = "p"
SUMMARISE = "s"


def main(args):
    datasets_to_run = []
    if args.type == PUBLISH:
        ds = Publication(name=args.name)
        if args.collated:
            args.flags += "c"
    elif args.type == SUMMARISE:
        ds = ReSummarise(name=args.name)
    else:
        raise Exception("invalid type")

    datasets_to_run.append(ds)

    run(datasets_to_run, args)


def setup():
    parser = argparse.ArgumentParser("Re_ Scheduler - for reprocessing sub parts of a run")
    parser.add_argument("type", type=str,
                        help=f"Single character to denote thing to redo - {PUBLISH} = publish, "
                             f"{SUMMARISE} = summarise")
    parser.add_argument("name", type=str, help="name for the dataset / collated derivative")
    parser.add_argument("-c", "--collated", action="store_true",
                        help="bool If True will treat the name as a collated derivative rather "
                             "than a dataset - only applies for publishing")
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
