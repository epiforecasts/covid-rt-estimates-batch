from definitions.date_standards import DATETIME_NOWISH


def generate_task_name(name: str):
    """
        Consistent function to define task naming format in one place
        Currently uses DATETIME_NOWISH to put a timestamp on the file - this should get set at
        script init so will be constant for the script run.
    :param name: string
    :return: string
    """
    return f"{DATETIME_NOWISH}_{name}"
