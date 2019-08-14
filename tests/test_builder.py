from unittest import TestCase
from simplebuilder import Builder
import os


class MyBuilder(Builder):

    def __init__(self):
        super().__init__()

        self.logger.setLevel('DEBUG')

        self.tasks = [
            {
                'name': 'folder',
                'outputs': ['testfolder'],
                'action': self.mkfolder,
                'flags': Builder.PRESENT  # Up to date of output is present
            }
        ]

    def mkfolder(self, t):
        os.mkdir(t['outputs'][0])


class MyBuilder2(MyBuilder):

    def __init__(self):
        super().__init__()

        self.tasks += [
            {
                'name': 'afile',
                'reqs': ['testfolder'],
                'outputs': ['testfolder/testfile'],
                'action': self.mkfile
            }
        ]

    def mkfile(self, t):
        with open(t['outputs'][0], 'w') as f:
            f.write('Hello world!')


class TestBuilder(TestCase):

    def test_flags1(self):

        builder = MyBuilder()
        try:
            os.rmdir(builder.tasks[0]['outputs'][0])
        except FileNotFoundError:
            pass
        self.assertTrue(builder.run('folder'))
        self.assertFalse(builder.run('folder'))
        os.rmdir(builder.tasks[0]['outputs'][0])

    def test_default(self):

        builder = MyBuilder()
        builder.default_task = 'folder'
        try:
            os.rmdir(builder.tasks[0]['outputs'][0])
        except FileNotFoundError:
            pass
        self.assertTrue(builder.run())
        self.assertFalse(builder.run())
        os.rmdir(builder.tasks[0]['outputs'][0])

    def test_flagdeps(self):

        builder = MyBuilder2()
        try:
            os.remove(builder.tasks[1]['outputs'][0])
        except FileNotFoundError:
            pass

        try:
            os.rmdir(builder.tasks[0]['outputs'][0])
        except FileNotFoundError:
            pass

        self.assertTrue(builder.run('afile'))
        self.assertFalse(builder.run('afile'))

        os.remove(builder.tasks[1]['outputs'][0])
        os.rmdir(builder.tasks[0]['outputs'][0])

    def test_flagdeps2(self):

        builder = MyBuilder2()
        try:
            os.remove(builder.tasks[1]['outputs'][0])
        except FileNotFoundError:
            pass

        try:
            os.rmdir(builder.tasks[0]['outputs'][0])
        except FileNotFoundError:
            pass

        self.assertTrue(builder.run('afile'))
        self.assertFalse(builder.run('afile'))

        os.remove(builder.tasks[1]['outputs'][0])
        os.rmdir(builder.tasks[0]['outputs'][0])