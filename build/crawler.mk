CRAWLER_CONN = host=$(POSTGRES_CONTAINER) user=postgres password=$(POSTGRES_PASSWORD) dbname=crawler

crawler-lottery: \
	crawler/TWN_lottery

crawler-stock: \
	crawler/TWN_twse \
	crawler/TWN_twse-taiex \
	crawler/TWN_twse-daily \
	crawler/TWN_twse-daily-individual \
	crawler/TWN_tpex-tpex \
	crawler/TWN_tpex-daily \
	crawler/TWN_tpex-daily-individual


$(shell ls -1 app/crawler | awk -F. '{print $$1}' | xargs -I{{}} echo crawler/{{}}):
	sudo docker container rm -f $(CODENAME)-$(@D)-$(@F) || true
	sudo docker run $(CRON_ARGS) --name $(CODENAME)-$(@D)-$(@F) \
		-v $(DIR_HOME)/app/crawler:/app \
		--link $(POSTGRES_CONTAINER) \
		$(ANACONDA_IMG) \
		python /app/$(@F).py '$(CRAWLER_CONN)'

crawler-database-init:
	sudo docker exec -it $(POSTGRES_CONTAINER) psql -U postgres -w -c 'CREATE DATABASE crawler'
