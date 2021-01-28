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


postgres/readonly:
	@ sudo docker exec -it $(POSTGRES_CONTAINER) psql -U postgres -w -c " \
		CREATE ROLE $(POSTGRES_READONLY_USER) WITH LOGIN PASSWORD '$(POSTGRES_READONLY_PASSWORD)'; \
		GRANT CONNECT ON DATABASE crawler TO $(POSTGRES_READONLY_USER); \
		"
	@ sudo docker exec -it $(POSTGRES_CONTAINER) psql -U postgres -w -d crawler -c " \
		GRANT USAGE ON SCHEMA public TO $(POSTGRES_READONLY_USER); \
		GRANT SELECT ON ALL TABLES IN SCHEMA public TO $(POSTGRES_READONLY_USER); \
		"
postgres/readonly-remove:
	@ sudo docker exec -it $(POSTGRES_CONTAINER) psql -U postgres -w -d crawler -c " \
		REVOKE ALL ON ALL TABLES IN SCHEMA public FROM $(POSTGRES_READONLY_USER); \
		REVOKE ALL ON SCHEMA public FROM $(POSTGRES_READONLY_USER); \
		"
	@ sudo docker exec -it $(POSTGRES_CONTAINER) psql -U postgres -w -c " \
		REVOKE ALL ON DATABASE crawler FROM $(POSTGRES_READONLY_USER); \
		DROP USER $(POSTGRES_READONLY_USER); \
		"
