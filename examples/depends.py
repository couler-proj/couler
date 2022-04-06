"""
This example demonstrates how to use "depends".

"depends" is an extension on "dependencies" to leverage the 
Workflow State as conditions: 
https://argoproj.github.io/argo-workflows/enhanced-depends-logic/ 
"""

import sys
import couler.argo as couler

from couler.argo_submitter import ArgoSubmitter
from typing import Callable

def random_code() -> None:
    """
    Randomly generate a 'success' or 'fail'
    to let sys.exit emulate a task final state
    """
    import random
    task = ['success', 'fail']
    res = random.randint(0, 1)
    res = task[res]
    print(f'{res}')
    if res == 'fail':
        sys.exit(2)


def job(name: str, source: Callable) -> Callable:    
    """
    Create a Workflow run_script job template
    """
    return couler.run_script(
        image="python:alpine3.6",
        source=source,
        step_name=name,
    )

# called if any task succeeded
def any_succeeded() -> None:
    print('A Task Succeeded')

# called if all tasks fail
def all_failed() -> None:
    print('All Tasks Failed')


def run_dag() -> None:
    """
    Create a DAG to submit to Argo Workflows
    """

    couler.set_dependencies(
        lambda: job(name='task1', source=random_code), 
        dependencies=None
    )
    
    couler.set_dependencies(
        lambda: job(name='task2', source=random_code), 
        dependencies='task1.Failed'
    )

    couler.set_dependencies(
        lambda: job(name='task3', source=random_code), 
        dependencies='task2.Failed'
    )

    couler.set_dependencies(
        lambda: job(name='task4', source=random_code), 
        dependencies='task3.Failed'
    )
    
    couler.set_dependencies(
        lambda: job(name='allfail', source=all_failed), 
        dependencies='task1.Failed && task2.Failed && task3.Failed && task4.Failed'
    )
    
    couler.set_dependencies(
        lambda: job(name='anysucceeded', source=any_succeeded), 
        dependencies='task1.Succeeded || task2.Succeeded || task3.Succeeded || task4.Succeeded'
    )


if __name__ == '__main__':
    run_dag()
    submitter = ArgoSubmitter()
    couler.run(submitter=submitter)
