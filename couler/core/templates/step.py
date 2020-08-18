from collections import OrderedDict

from couler.core import pyfunc
from couler.core.templates.template import Template


class Step(object):
    def __init__(
        self, name, template=None, arguments=None, when=None, with_itmes=None
    ):
        self.name = name
        self.template = template
        self.arguments = arguments
        self.with_items = with_itmes
        self.when = when

    def to_dict(self):
        d = OrderedDict({"name": self.name})
        if self.template is not None:
            d.update({"template": self.template})
        if self.when is not None:
            d.update({"when": self.when})
        if pyfunc.non_empty(self.arguments):
            d.update({"arguments": self.arguments})
        if pyfunc.non_empty(self.with_items):
            d.update({"withItems": self.with_items})
        return d


class Steps(Template):
    def __init__(self, name, steps=None):
        Template.__init__(self, name=name)
        self.steps = steps

    def to_dict(self):
        template = Template.to_dict(self)
        template["steps"] = self.steps
        return template
