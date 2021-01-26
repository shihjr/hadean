GCC_IMG       = gcc:latest
GCC_CONTAINER = $(CODENAME)-gcc

gcc:
	sudo docker container rm -f $(GCC_CONTAINER) || true
	sudo docker pull $(GCC_IMG)
	sudo docker run --user $$(id -u) -it --name $(GCC_CONTAINER) \
		-w $(DIR_HOME) \
		-v $(DIR_HOME):$(DIR_HOME) \
		$(GCC_IMG) /bin/bash
