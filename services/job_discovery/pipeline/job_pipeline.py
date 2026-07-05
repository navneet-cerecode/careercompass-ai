"""
Job Pipeline.

Runs every processing stage on discovered jobs.
"""

from models.job import Job


class JobPipeline:
    """
    Executes processing stages on jobs.
    """

    def __init__(self):

        self.stages = []

    def add_stage(
        self,
        stage,
    ):

        self.stages.append(stage)

    def process(
        self,
        jobs: list[Job],
    ) -> list[Job]:

        result = jobs

        for stage in self.stages:

            result = stage.process(
                result
            )

        return result