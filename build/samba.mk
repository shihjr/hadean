SAMBA_CFG      = /etc/samba/smb.conf

SAMBA_USERNAME = xxxxxx
SAMBA_PASSWORD = xxxxxx

samba: -samba/install -samba/config -samba/user -samba/service -samba/install
	@ :

-samba/install:
	sudo apt -y install samba

-samba/config:
	grep $(SAMBA_USERNAME) $(SAMBA_CFG) || sudo echo -e \
		'[$(SAMBA_USERNAME)]\n' \
		'  comment =\n' \
		'  browseable = yes\n' \
		'  path = /home/$(SAMBA_USERNAME)\n' \
		'  printable = no\n' \
		'  guest ok = no\n' \
		'  read only = no\n' \
		'  create mask = 0700' >> $(SAMBA_CFG)

-samba/user:
	echo -ne '$(SAMBA_PASSWORD)\n$(SAMBA_PASSWORD)\n' | sudo smbpasswd -a -s $(SAMBA_USERNAME)

-samba/service:
	sudo service smbd restart
