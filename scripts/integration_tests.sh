python -m integration_tests.dag_example
python -m integration_tests.flip_coin_example
# Validate workflow statuses
kubectl -n argo get workflows
for WF_NAME in $(kubectl -n argo get workflows --no-headers -o custom-columns=":metadata.name")
do
    bash scripts/validate_workflow_statuses.sh ${WF_NAME}
done
