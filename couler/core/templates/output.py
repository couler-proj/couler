# Copyright 2021 The Couler Authors. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import attr


@attr.s
class Output(object):
    # value = attr.ib(default=None)
    name = attr.ib()
    step_name: str = attr.ib()
    template_name: str = attr.ib()
    is_global: bool = attr.ib(default=False)

    def value(self, type):
        if self.is_global:
            return "workflow.outputs.%s.%s" % (type, self.name)
        else:
            return "%s.%s.outputs.%s.%s" % (
                self.step_name,
                self.template_name,
                type,
                self.name,
            )

    def placeholder(self, prefix, type):
        if self.is_global:
            return '"{{workflow.outputs.%s.%s.%s}}"' % (
                self.step_name,
                type,
                self.name,
            )
        else:
            return '"{{%s.%s.outputs.%s.%s}}"' % (
                prefix,
                self.step_name,
                type,
                self.name,
            )


@attr.s
class OutputEmpty(Output):
    pass


@attr.s
class OutputParameter(Output):
    path = attr.ib(default="")

    def to_yaml(self):
        return {"name": self.name, "valueFrom": {"path": self.path}}

    @property
    def value(self):
        return super().value("parameters")

    def placeholder(self, prefix):
        return super().placeholder(prefix, "parameters")


@attr.s
class OutputArtifact(Output):
    path = attr.ib(default="")
    artifact = attr.ib(default={})
    type = attr.ib(default="")

    @property
    def value(self):
        return super().value("artifacts")

    def placeholder(self, prefix):
        return super().placeholder(prefix, "artifacts")


@attr.s
class OutputScript(Output):
    @property
    def value(self):
        return "%s.%s.outputs.result" % (self.step_name, self.template_name)

    def placeholder(self, prefix, type):
        return '"{{%s.%s.outputs.result}}"' % (prefix, self.step_name)


@attr.s
class OutputJob(Output):
    job_name = attr.ib(default="job")
    job_id = attr.ib(default="job_id")
    job_obj = attr.ib(default=None)


def _parse_single_argo_output(output, prefix):
    if isinstance(output, Output):
        tmp = output.value.split(".")
        if "artifacts" in tmp:
            return output
        if len(tmp) < 4:
            raise ValueError("Incorrect step return representation")
        step_name = tmp[1]
        output_id = tmp[3]
        for item in tmp[4:]:
            output_id = output_id + "." + item
        if output.is_global:
            return '"{{workflow.outputs.%s}}"' % output_id
        else:
            return '"{{%s.%s.%s}}"' % (prefix, step_name, output_id)
    else:
        # enforce int, float and bool types to string
        if (
            isinstance(output, int)
            or isinstance(output, float)
            or isinstance(output, bool)
        ):
            output = "'%s'" % output

        return output


def parse_argo_output(output, prefix):
    if isinstance(output, OutputJob):
        return [
            _parse_single_argo_output(
                Output(value=output.job_id, is_global=output.is_global), prefix
            ),
            _parse_single_argo_output(
                Output(value=output.job_name, is_global=output.is_global),
                prefix,
            ),
            _parse_single_argo_output(
                Output(value=output.job_obj, is_global=output.is_global),
                prefix,
            ),
        ]
    else:
        return _parse_single_argo_output(output, prefix)


def _container_param_output(output_object, step_name, template_name):
    is_global = "globalName" in output_object
    return OutputParameter(
        name=output_object["name"],
        step_name=step_name,
        template_name=template_name,
        is_global=is_global,
    )


def _container_artifact_output(output_object, step_name, template_name):
    is_global = "globalName" in output_object
    return OutputArtifact(
        name=output_object["name"],
        step_name=step_name,
        template_name=template_name,
        path=output_object["path"],
        artifact=output_object,
        is_global=is_global,
    )


def _container_output(step_name, template_name, output):
    """Generate output name from an Argo container template.  For example,
    "{{steps.generate-parameter.outputs.parameters.hello-param}}" used in
    https://github.com/argoproj/argo/tree/master/examples#output-parameters.
    Each element of return for run_container is contacted by:
    couler.step_name.template_name.output.parameters.output_id
    """

    if output is None:
        return {
            "parameters": [
                OutputEmpty(
                    name="%s-empty-output" % template_name,
                    step_name=step_name,
                    template_name=template_name,
                )
            ]
        }

    return {
        "parameters": [
            _container_param_output(
                output_object=o,
                step_name=step_name,
                template_name=template_name,
            )
            for o in output["parameters"]
        ],
        "artifacts": [
            _container_artifact_output(
                output_object=o,
                step_name=step_name,
                template_name=template_name,
            )
            for o in output["artifacts"]
        ],
    }


def _script_output(step_name, template_name, output):
    """Generate output name from an Argo script template.  For example,
    "{{steps.generate.outputs.result}}" in
    https://github.com/argoproj/argo/tree/master/examples#scripts--results
    Return of run_script is contacted by:
    couler.step_name.template_name.outputs.result
    """
    output_script = OutputScript(
        name="script-output", step_name=step_name, template_name=template_name
    )

    if output is None:
        return [output_script]

    rets = _container_output(step_name, template_name, output)
    rets.append(output_script)

    return rets


def _job_output(step_name, template_name):
    """
    :param step_name:
    :param template_name:
    https://github.com/argoproj/argo/blob/master/examples/k8s-jobs.yaml#L44
    Return the job name and job id for running a job
    """
    job_name = "couler.%s.%s.outputs.parameters.job-name" % (
        step_name,
        template_name,
    )
    job_id = "couler.%s.%s.outputs.parameters.job-id" % (
        step_name,
        template_name,
    )
    job_obj = "couler.%s.%s.outputs.parameters.job-obj" % (
        step_name,
        template_name,
    )

    return [
        OutputJob(
            value=job_name, job_name=job_name, job_obj=job_obj, job_id=job_id
        )
    ]


def extract_step_return(step_output):
    """Extract information for run container or script output.
    step_output is a list with multiple outputs
    """

    ret = {}
    if isinstance(step_output, list):
        # The first element of outputs is used for control flow operation
        step_output = step_output[0]
        # In case user input a normal variable
        if isinstance(step_output, Output):
            tmp = step_output.value.split(".")
            if len(tmp) < 4:
                raise ValueError("Incorrect step return representation")
            # To avoid duplicate map function
            output = tmp[2]
            for item in tmp[3:]:
                output = output + "." + item

            ret = {
                "name": step_output.template_name,
                "id": step_output.step_name,
                "output": output,
            }

            return ret
        else:
            ret["value"] = step_output
            return ret
    else:
        ret["value"] = step_output
        return ret
