# Couler Releases

## Release v0.1.1rc6

This release includes several bug fixes and enhancements. Below are some of the notable changes:

* Bump the dependency of Argo Python client to v3.5.1 and re-enable Argo Workflow spec validation.
* Fix incorrect `ApiException` import path for Kubernetes Python client with version 11.0.0 and above.
* Support `callable` for Couler core APIs in stead of previously only `types.FunctionType`.
* Switch to use Argo Workflows v2.10.2 for integration tests.

## Release v0.1.1rc5

This is the initial public release with Argo Workflows support.
