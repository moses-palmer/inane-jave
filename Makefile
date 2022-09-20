NAMESPACE := $(USER)
PROJECT := "inane-jave"
VERSION := $(shell cat backend/VERSION)
UID := $(shell id --user $(USER))


.PHONY: container
container: Dockerfile
	@docker build . \
		--build-arg UID=$(UID) \
		--tag $(NAMESPACE)/$(PROJECT):$(VERSION)
