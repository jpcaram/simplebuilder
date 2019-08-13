import os
from subprocess import check_output


class CannotBuildError(Exception):
    pass


class Builder:

    def __init__(self):
        pass

    def get_task_by_name(self, name):
        for task in self.tasks:
            if 'name' in task and task['name'] == name:
                return task
        return None

    def get_task_by_output(self, output):
        for task in self.tasks:
            if 'outputs' in task and output in task['outputs']:
                return task

    def run_(self, t):
        # print('run({})'.format(str(t)))

        task = None

        if isinstance(t, dict):
            task = t

        if task is None:
            task = self.get_task_by_name(t)

        if task is None:
            task = self.get_task_by_output(t)

        if task is None:
            raise RuntimeError('Task not found: {}'.format(t))

        # print('requirement...')
        # Requirements?
        reqtasks = []
        if 'reqs' in task:
            for req in task['reqs']:
                reqtask = self.get_task_by_output(req)
                if reqtask is not None and reqtask not in reqtasks:
                    self.run_(reqtask)
                    reqtasks.append(reqtask)
        # print("{} req. tasks.".format(len(reqtasks)))
        
        if 'reqs' not in task:
            # TODO: Must define how to handle. Force make for now.
            if 'action' in task:
                task['action'](task)
                return
            else:
                raise CannotBuildError("No action to build target")
                return
        
        # print('timestamps...')
        # Check timestamps
        try:
            newest_req_t = max([os.path.getmtime(o) for o in task['reqs']])
        except FileNotFoundError as e:
            raise CannotBuildError(str(e))
            # return

        # print("Requirement timestamps done.")
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
            return

        # print("Comparing time-stamps...")
        if newest_req_t > oldest_output_t:
            # Requirement is newer, run actions
            if 'action' in task:
                task['action'](task)
                return
            else:
                raise CannotBuildError("No action to build target")

        print('Up to date.')

    def run(self, t):

        try:
            self.run_(t)
        except CannotBuildError as e:
            print("ERROR: Could not build out-of-date target: {}".format(str(e)))