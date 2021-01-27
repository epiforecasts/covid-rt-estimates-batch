from definitions.date_standards import DAILY


class Processable:
    def __init__(self, name: str, max_wall_clock_minutes: int, base_fn: str):
        self.base_fn = base_fn
        self.max_wall_clock_minutes = max_wall_clock_minutes
        self.name = name


class ScheduledProcessable(Processable):
    def __init__(self, name: str, data_dir: str, frequency: list,
                 max_wall_clock_minutes: int, base_fn: str):
        super().__init__(
                name=name,
                max_wall_clock_minutes=max_wall_clock_minutes,
                base_fn=base_fn
                )
        self.frequency = frequency if frequency else DAILY
        self.data_dir = data_dir


class Dataset(ScheduledProcessable):
    def __init__(self, name: str, data_dir: str, frequency: list = None,
                 timeout: int = 21600, max_wall_clock_minutes: int = 600):
        super().__init__(
                name=name,
                data_dir=data_dir,
                frequency=frequency,
                max_wall_clock_minutes=max_wall_clock_minutes,
                base_fn='Rscript R/run-region-updates.R'
                )
        self.timeout = timeout


class Derivative(ScheduledProcessable):
    def __init__(self, name: str, data_dir: str, dependencies: list,
                 frequency: list = None,
                 max_wall_clock_minutes: int = 30):
        super().__init__(
                name=name,
                data_dir=data_dir,
                frequency=frequency,
                max_wall_clock_minutes=max_wall_clock_minutes,
                base_fn='Rscript R/run-collate-derivative.R'
                )
        self.dependencies = dependencies


class Publication(Processable):
    def __init__(self, name: str, is_derivative: bool = False):
        super().__init__(
                name=name,
                max_wall_clock_minutes=30,
                base_fn='Rscript R/run-republish.R'
                )
        self.is_derivative = is_derivative


class ReSummarise(Processable):
    def __init__(self, name: str):
        super().__init__(
                name=name,
                max_wall_clock_minutes=30,
                base_fn='Rscript R/run-resummarise.R'
                )
