
PWD = $(shell pwd)
APP = libvirt-test-API

all: libvirt-test-api

libvirt-test-api:

.PHONY: dist clean
dist:
	@rm -rf /tmp/$(APP)
	@cp -r $(PWD) /tmp/$(APP)
	@find /tmp/$(APP) -name "*.pyc" -exec rm -f {} \; 
	@cd /tmp/$(APP); rm -rf .git/ log/; rm -f .gitignore log.xml
	@chmod +x /tmp/$(APP)/libvirt-test-api.py
	@cd /tmp; tar czSpf $(APP).tar.gz $(APP)
	@rm -rf /tmp/$(APP)
	@cp /tmp/$(APP).tar.gz .
	@rm -f /tmp/$(APP).tar.gz
	@echo " "
	@echo "the archive is $(APP).tar.gz"

clean:
	@find . -name "*.pyc" -exec rm -f {} \;
	@rm -rf log/ log.xml
	@rm -f $(APP).tar.gz
