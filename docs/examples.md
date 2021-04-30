# Examples

### Hello World!

Let's start by running a very simple workflow template to echo "hello world" using the `docker/whalesay` container image from DockerHub.

You can run this directly from your shell with a simple docker command:

```
$ docker run docker/whalesay cowsay "hello world"
 _____________
< hello world >
 -------------
    \
     \
      \
                    ##        .
              ## ## ##       ==
           ## ## ## ##      ===
       /""""""""""""""""___/ ===
  ~~~ {~~ ~~~~ ~~~ ~~~~ ~~ ~ /  ===- ~~~
       \______ o          __/
        \    \        __/
          \____\______/
```

With Couler, we can run the same container on a Kubernetes cluster 
using an Argo Workflows as the workflow engine.

```python
--8<-- "examples/hello_world.py"
```

### Coin Flip

This example combines the use of a Python function result, along with conditionals,
to take a dynamic path in the workflow. In this example, depending on the result
of the first step defined in `flip_coin()`, the template will either run the
`heads()` step or the `tails()` step.

Steps can be defined via either `couler.run_script()`
for Python functions or `couler.run_container()` for containers. In addition,
the conditional logic to decide whether to flip the coin in this example
is defined via the combined use of `couler.when()` and `couler.equal()`.

```python
--8<-- "examples/coin_flip.py"
```

### DAG

This example demonstrates different ways to define the workflow as a directed-acyclic graph (DAG) by specifying the
dependencies of each task via `couler.set_dependencies()` and `couler.dag()`. Please see the code comments for the
specific shape of DAG that we've defined in `linear()` and `diamond()`.

```python
--8<-- "examples/dag.py"
```

Note that the current version only works with Argo Workflows but we are actively working on the design of the unified
interface that is extensible to additional workflow engines. Please stay tuned for more updates and we welcome
any feedback and contributions from the community.
