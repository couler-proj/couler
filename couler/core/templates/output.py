class Output(object):
    def __init__(self, value, is_global=False):
        self.value = value
        self.is_global = is_global


class OutputEmpty(Output):
    def __init__(self, value, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)


class OutputParameter(Output):
    def __init__(self, value, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)


class OutputArtifact(Output):
    def __init__(self, value, path, artifact, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)
        self.path = path
        self.artifact = artifact


class OutputScript(Output):
    def __init__(self, value, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)


class OutputJob(Output):
    def __init__(self, value, job_name, job_id, job_obj=None, is_global=False):
        Output.__init__(self, value=value, is_global=is_global)
        self.job_name = job_name
        self.job_id = job_id
        self.job_obj = job_obj
