import os
from typing import List, Dict


class CannotBuildError(Exception):
    pass


class Builder:

    def __init__(self):
        self.tasks: List[Dict] = []

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

    def run_(self, t):

        task = None

        if isinstance(t, dict):
            task = t

        if task is None:
            task = self.get_task_by_name(t)

        if task is None:
            task = self.get_task_by_output(t)

        if task is None:
            raise RuntimeError('Task not found: {}'.format(t))

        # Requirements?
        reqtasks = []
        if 'reqs' in task:
            for req in task['reqs']:
                reqtask = self.get_task_by_output(req)
                if reqtask is not None and reqtask not in reqtasks:
                    self.run_(reqtask)
                    reqtasks.append(reqtask)

        if 'reqs' not in task:
            # TODO: Must define how to handle. Force make for now.
            if 'action' in task:
                task['action'](task)
                return
            else:
                raise CannotBuildError("No action to build target")
                # return

        # Check timestamps
        try:
            newest_req_t = max([os.path.getmtime(o) for o in task['reqs']])
        except FileNotFoundError as e:
            raise CannotBuildError(str(e))
            # return

        try:
            oldest_output_t = min([os.path.getmtime(o) for o in task['outputs']])
        except FileNotFoundError as e:
            # Missing output, must run
            # print('Missing output!')
            if 'action' in task:
                task['action'](task)
                return
            else:
                raise CannotBuildError("No action to build target")
            # return

        if newest_req_t > oldest_output_t:
            # Requirement is newer, run actions
            if 'action' in task:
                task['action'](task)
                return
            else:
                raise CannotBuildError("No action to build target")

        print('Up to date.')

    def run(self, t):
        """
        Run a task.

        :param t: Task specification. Can be a task name, or an output generated by
            some task.
        :return: None
        """

        try:
            self.run_(t)
        except CannotBuildError as e:
            print("ERROR: Could not build out-of-date target: {}".format(str(e)))

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