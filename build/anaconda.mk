ANACONDA_IMG = $(CODENAME)-anaconda

anaconda-prerequisites:
	sudo docker build -t $(ANACONDA_IMG) -f build/docker/anaconda.dockerfile . \
		--no-cache --pull --rm
