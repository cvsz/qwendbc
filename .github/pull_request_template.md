## Summary

Describe the behavior change and why it is needed. Link related issues where applicable.

## Validation

Check the gates you ran locally or explain why a gate is not applicable:

- [ ] `make lint`
- [ ] `make test`
- [ ] `make security`
- [ ] `make shellcheck` (required when shell scripts are present)
- [ ] `make docker-build`

## Change type

- [ ] Bug fix
- [ ] Feature
- [ ] Refactor
- [ ] Documentation
- [ ] Dependency / tooling
- [ ] Security hardening
- [ ] Breaking change

## Security / data considerations

- [ ] No credentials, `.env`, local model files, or private data are committed.
- [ ] New network-exposed behavior has explicit validation/access-control considerations.
- [ ] Dependency/model supply-chain changes are identified.
- [ ] Sensitive vulnerability details were coordinated privately before public disclosure, if applicable.

## Compatibility

Note any Python, Node, Docker, model, API, configuration, or migration impact.
