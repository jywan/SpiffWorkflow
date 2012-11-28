# Copyright (C) 2012 Matthew Hampton
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
from collections import deque

import logging
from SpiffWorkflow.Task import Task
from SpiffWorkflow.bpmn.specs.BpmnSpecMixin import BpmnSpecMixin
from SpiffWorkflow.specs.Join import Join

LOG = logging.getLogger(__name__)

class ParallelGateway(Join, BpmnSpecMixin):
    """
    Task Spec for a bpmn:parallelGateway node.
    """

    def _try_fire_unstructured(self, my_task, force=False):
        # Look at the tree to find all ready and waiting tasks (excluding ourself).
        tasks = []
        for task in my_task.workflow.get_tasks(Task.READY | Task.WAITING):
            if task.thread_id != my_task.thread_id:
                continue
            if task.task_spec == my_task.task_spec:
                continue
            tasks.append(task)

        # Are any of those tasks a potential ancestor to this task?
        waiting_tasks = []
        for task in tasks:
            if self._is_descendant(self, task):
                waiting_tasks.append(task)

        return force or len(waiting_tasks) == 0, waiting_tasks

    def _is_descendant(self, task_spec, task):
        q = deque()
        done = set()

        #We must skip ancestors of the task - so that loops don't make everything a descendent of everything!
        p = task.parent
        while (p != None and not p.task_spec in done):
            done.add(p.task_spec)
            p = p.parent

        q.append(task.task_spec)
        while q:
            n = q.popleft()
            if n == task_spec:
                return True
            for child in n.outputs:
                if child not in done:
                    done.add(child)
                    q.append(child)
        return False


    def _update_state_hook(self, my_task):
        if my_task._is_predicted():
            self._predict(my_task)
        if not my_task.parent._is_finished():
            return

        super(ParallelGateway, self)._update_state_hook(my_task)