from couler.core import states
from couler.core.templates.volume import Volume


def add_volume(volume: Volume):
    """
    Add existing volume to the workflow.

    Reference:
    https://github.com/argoproj/argo/blob/master/examples/volumes-existing.yaml
    """
    states.workflow.add_volume(volume)
