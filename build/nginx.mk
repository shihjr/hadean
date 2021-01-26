NGINX_IMG       = nginx:latest
NGINX_CONTAINER = $(CODENAME)-nginx

NGINX_DATA      = $(DIR_DATA)/nginx

nginx: -nginx-docker/$(NGINX_CONTAINER)
	test -f $(NGINX_DATA) || mkdir -p $(NGINX_DATA)

	sudo docker run --name $(NGINX_CONTAINER) -d \
		-p 443:443 \
		-v $(DIR_HOME)/conf/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
		-v $(DIR_HOME)/conf/nginx/$(DOMAIN_NAME).conf:/etc/nginx/conf.d/host.conf:ro \
		-v $(DIR_HOME)/$(CERTBOT_DIR):/etc/letsencrypt:ro \
		-v $(NGINX_DATA):/var/log/nginx \
		$(NGINX_IMG)

-nginx-docker/%:
	sudo docker container rm -f $(@F) || true
	sudo docker pull $(NGINX_IMG)
