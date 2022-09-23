NAMESPACE := $(USER)
PROJECT := "inane-jave"
VERSION := $(shell cat backend/VERSION)
UID := $(shell id --user $(USER))


all: container ijave


.PHONY: container
container: Dockerfile
	@docker build . \
		--build-arg UID=$(UID) \
		--tag $(NAMESPACE)/$(PROJECT):$(VERSION)


ijave: ijave.in backend/VERSION
	@sed \
		-e s/@NAMESPACE@/$(NAMESPACE)/g \
		-e s/@PROJECT@/$(PROJECT)/g \
		-e s/@VERSION@/$(VERSION)/g \
		< ijave.in \
		> ijave
	@chmod a+x ijave


test: test.in container backend/VERSION
	@sed \
		-e s/@NAMESPACE@/$(NAMESPACE)/g \
		-e s/@PROJECT@/$(PROJECT)/g \
		-e s/@VERSION@/$(VERSION)/g \
		< test.in \
		> test
	@sh test
