import os
from typing import List, Dict
import logging
import sys


class CannotBuildError(Exception):
    pass


class Builder:

    ALWAYS = 1
    """Always run the task's action regardless of requirements and outputs."""

    PRESENT = 2
    """Targets must be present for the task to be up to date."""

    OLDER = 4
    """Targets must be older than requiring tasks targets for a task to
    be considered up to date."""

    IGNOREPRESENT = 8
    """If a requirement has the PRESENT flag, ignore its date."""

    def __init__(self):

        self.logger = logging.getLogger('Builder')
        self.logger.setLevel(logging.ERROR)
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(h)
        self.logger.debug(f'{self.__class__.__name__}.__init__()')

        self.tasks: List[Dict] = []
        """List of tasks"""

        self.default_task = None
        """Name of the default task"""

    def get_task_by_name(self, name):
        """
        Get the task definition with the given name.

        :param name: str - name of the task.
        :return: Task definition or None if it does not exist.
        """

        for task in self.tasks:
            if 'name' in task and task['name'] == name:
                return task
        return None

    def get_task_by_output(self, output):
        """
        Get the task that generates the specified output. This means, output
        is listed in the task's definition output list.

        :param output: An output generated by some task/
        :return: Task definition or None.
        """

        for task in self.tasks:
            if 'outputs' in task and output in task['outputs']:
                return task

    def run_(self, t=None):
        """
        Internal run method.

        :param t: Task name or definition
        :return: True if the task ran. False otherwise.
        """

        self.logger.debug(f'{self.__class__.__name__}.run_({t})')

        # Run the default task if not specified.
        t = t or self.default_task

        task = None

        if isinstance(t, dict):
            task = t

        if task is None:
            task = self.get_task_by_name(t)

        if task is None:
            task = self.get_task_by_output(t)

        if task is None:
            raise RuntimeError('Task not found: {}'.format(t))

        # Requirements? If so, recurse into them.
        reqtasks = []
        req_dates = []
        newest_req_t = 0  # Beginning of times.
        if 'reqs' in task:
            for req in task['reqs']:
                reqtask = self.get_task_by_output(req)
                if reqtask is not None and reqtask not in reqtasks:
                    self.run_(reqtask)  # Run requirement task
                    reqtasks.append(reqtask)

            # Newest (in time) requirement
            try:
                req_dates = []
                for req in task['reqs']:
                    rtask = self.get_task_by_output(req)

                    # This requirement is not to be ignored?
                    if (not rtask) or \
                            ('flags' not in rtask) or \
                            ('flags' not in task) or \
                            not (Builder.IGNOREPRESENT & task['flags']):
                        req_dates.append(os.path.getmtime(req))
                newest_req_t = max(req_dates)
            except FileNotFoundError as e:
                raise CannotBuildError(str(e))
            except ValueError as e:
                pass  # req_dates is empty.

        # This task does not have requirements, or all requirements
        # are ignored in the date comparison.
        if 'reqs' not in task or len(req_dates) == 0:
            # TODO: Must define how to handle. Force make for now.
            if 'action' in task:
                if ('flags' not in task) or (Builder.ALWAYS & task['flags']):
                    task['action'](task)
                    return True
                if Builder.PRESENT & task['flags']:
                    try:
                        [os.path.getmtime(o) for o in task['outputs']]
                    except FileNotFoundError:
                        self.logger.info(task['name'] + ' is NOT up to date. Running.')
                        task['action'](task)
                        return True
                    self.logger.info(task['name'] + ' is up to date.')
                    return False  # Did not run
            else:
                raise CannotBuildError("No action to build target")

        # Oldest output
        try:
            oldest_output_t = min([os.path.getmtime(o) for o in task['outputs']])
        except FileNotFoundError as e:
            # Missing output, must run
            if 'action' in task:
                self.logger.info(task['name'] + ' is NOT up to date. Running.')
                task['action'](task)
                return True
            else:
                raise CannotBuildError("No action to build target")

        # All outputs are present. Now let's compare dates with the requirements.
        if newest_req_t > oldest_output_t:
            # Requirement is newer, run actions
            if 'action' in task:
                self.logger.info(task['name'] + ' is NOT up to date. Running.')
                task['action'](task)
                return True
            else:
                raise CannotBuildError("No action to build target")

        self.logger.info(task['name'] + ' is up to date.')
        return False  # Did not run

    def run(self, t=None):
        """
        Run a task.

        :param t: Task specification. Can be a task name, or an output generated by
            some task. If None (default) runs the default_task.
        :return: True if the task ran. False otherwise.
        """

        try:
            return self.run_(t=t)
        except CannotBuildError as e:
            self.logger.error("ERROR: Could not build out-of-date target: {}".format(str(e)))
            return False

    def clean(self, t=None):
        """
        Removes all the outputs of a task. If the task is not specified,
        all outputs of all tasks are removed.

        :param t: Task specification. Can be a task name, or an output generated by
            some task.
        :return: None
        """

        task = None

        if t is None:
            for t_ in self.tasks:
                self.clean(t=t_)

        if isinstance(t, dict):
            task = t

        if t is None:
            task = self.get_task_by_name(t)

        if t is None:
            task = self.get_task_by_output(t)

        if task is None:
            raise RuntimeError('Task not found: {}'.format(t))

        for op in task['outputs']:
            try:
                os.remove(op)
            except OSError:
                pass

