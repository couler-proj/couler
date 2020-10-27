class K8s:
    def __init__(self):
        pass

    def config_pod(self, template):
        template["tolerations"] = list()
        return template

    def config_workflow(self, spec):
        spec["hostNetwork"] = True
        return spec


cluster = K8s()
