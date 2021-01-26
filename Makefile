include conf.mk

CODENAME   = hadean
DIR_HOME  := $(shell pwd)

ETH       := $(shell ls -1 /sys/class/net/ | grep -v lo | grep -v docker | grep -v veth | grep -v ppp)
LOCAL_IP  := $(shell ip addr show $(ETH) | grep -Po 'inet \K[\d.]+')

DIR_DATA   = $(DIR_HOME)/data

CRON_ARGS ?= -it

SHELL      = /bin/bash

info:
	:

prerequisite:
	sudo apt -y update
	sudo apt -y upgrade
	sudo apt -y install docker.io
	sudo apt -y install net-tools

password:
	openssl rand -base64 32


backup:
	sudo tar Jcvf $(CODENAME)-data.tar.xz data
	mv $(CODENAME)-data.tar.xz $(BACKUP_DIR)/$(CODENAME)-`TZ=UTC-8 date "+%Y%m%d"`.tar.xz


server: postgres redis nginx


-include build/*.mk


cron:
	> .$@
	echo "00 19 * * * make -C $(DIR_HOME) backup" >> .$@
	echo "30 14 * * * make -C $(DIR_HOME) CRON_ARGS= crawler/TWN_lottery > $(DIR_HOME)/TWN_lottery.log 2>&1" >> .$@
	echo "30 07 * * * make -C $(DIR_HOME) CRON_ARGS= crawler/TWN_stock   > $(DIR_HOME)/TWN_stock.log 2>&1"   >> .$@
	crontab .$@
	rm .$@
	sudo service cron restart
