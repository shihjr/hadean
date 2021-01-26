CERTBOT_CONTAINER = $(CODENAME)-certbot
CERTBOT_DIR       = .certbot

certbot: -nginx-docker/$(CERTBOT_CONTAINER)
	test -f $(CERTBOT_DIR) || mkdir -p $(CERTBOT_DIR)
	cp conf/nginx/nginx.conf $(CERTBOT_DIR)
	cp conf/certbot/$(DOMAIN_NAME).conf $(CERTBOT_DIR)

	sudo docker run --name $(CERTBOT_CONTAINER) -d \
		-p 80:80 \
		-v $(DIR_HOME)/$(CERTBOT_DIR)/nginx.conf:/etc/nginx/nginx.conf \
		-v $(DIR_HOME)/$(CERTBOT_DIR)/$(DOMAIN_NAME).conf:/etc/nginx/conf.d/host.conf \
		-v $(DIR_HOME)/$(CERTBOT_DIR):/etc/letsencrypt \
		$(NGINX_IMG)

	sudo docker exec -it $(CERTBOT_CONTAINER) apt -y update
	sudo docker exec -it $(CERTBOT_CONTAINER) apt -y install certbot python-certbot-nginx
	sudo docker exec -it $(CERTBOT_CONTAINER) certbot --nginx \
		--non-interactive --agree-tos \
		-m $(EMAIL) \
		-d $(DOMAIN_NAME)

	sudo docker container rm -f $(CERTBOT_CONTAINER) || true

	rm -f $(CERTBOT_DIR)/nginx.conf
	rm -f $(CERTBOT_DIR)/$(DOMAIN_NAME).conf

certbot/xz:
	sudo tar Jcvf $(DOMAIN_NAME).tar.xz $(CERTBOT_DIR)
