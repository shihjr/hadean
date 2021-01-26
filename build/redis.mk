REDIS_IMG       = redis:latest
REDIS_CONTAINER = $(CODENAME)-redis

REDIS_DATA      = $(DIR_DATA)/redis

redis:
	sudo docker container rm -f $(REDIS_CONTAINER) || true
	sudo docker pull $(REDIS_IMG)
	sudo docker run -it --name $(REDIS_CONTAINER) -d \
		-v $(REDIS_DATA):/data \
		$(REDIS_PORT) \
		$(REDIS_IMG)
