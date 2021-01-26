pppoe: -pppoe/prerequisite -pppoe/conf
	@ :

-pppoe/prerequisite:
	sudo apt -y install pppoeconf

-pppoe/conf:
	sudo pppoeconf
