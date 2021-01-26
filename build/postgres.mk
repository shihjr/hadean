POSTGRES_IMG       = postgres:latest
POSTGRES_CONTAINER = $(CODENAME)-postgres

POSTGRES_DATA      = $(DIR_DATA)/postgres

postgres:
	test -f $(POSTGRES_DATA) || mkdir -p $(POSTGRES_DATA)

	sudo docker container rm -f $(POSTGRES_CONTAINER) || true
	sudo docker pull $(POSTGRES_IMG)
	@ sudo docker run -it --name $(POSTGRES_CONTAINER) -d \
		-v $(POSTGRES_DATA):/var/lib/postgresql/data \
		-e POSTGRES_PASSWORD="$(POSTGRES_PASSWORD)" \
		$(POSTGRES_PORT) \
		$(POSTGRES_IMG)

postgres/password:
	@ sudo docker exec -it $(POSTGRES_CONTAINER) psql -U postgres -w -c "ALTER USER postgres WITH PASSWORD '$(POSTGRES_PASSWORD)'"
