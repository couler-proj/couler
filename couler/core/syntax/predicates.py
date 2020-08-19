import types


def _predicate(pre, post, condition):
    """Generates an Argo predicate.
    """
    dict_config = {}
    if isinstance(pre, types.FunctionType):
        dict_config["pre"] = pre()
    else:
        dict_config["pre"] = pre

    if isinstance(post, types.FunctionType):
        dict_config["post"] = post()
    else:
        dict_config["post"] = post

    # TODO: check the condition
    dict_config["condition"] = condition

    return dict_config


def equal(pre, post=None):
    if post is not None:
        return _predicate(pre, post, "==")
    else:
        return _predicate(pre, None, "==")


def not_equal(pre, post=None):
    if post is not None:
        return _predicate(pre, post, "!=")
    else:
        return _predicate(pre, None, "!=")


def bigger(pre, post=None):
    if post is not None:
        return _predicate(pre, post, ">")
    else:
        return _predicate(pre, None, ">")


def smaller(pre, post=None):
    if post is not None:
        return _predicate(pre, post, "<")
    else:
        return _predicate(pre, None, "<")


def bigger_equal(pre, post=None):
    if post is not None:
        return _predicate(pre, post, ">=")
    else:
        return _predicate(pre, None, ">=")


def smaller_equal(pre, post=None):
    if post is not None:
        return _predicate(pre, post, "<=")
    else:
        return _predicate(pre, None, "<=")
