
PWD = $(shell pwd)
SUIT_NAME = libvirt-test-API

all: libvirt-test-api

libvirt-test-api:

.PHONY: dist clean
dist:
	@rm -rf /tmp/$(SUIT_NAME)
	@cp -r $(PWD) /tmp/$(SUIT_NAME)
	@find /tmp/$(SUIT_NAME) -name "*.pyc" -exec rm -f {} \; 
	@cd /tmp/$(SUIT_NAME); rm -rf .git/ log/; rm -f .gitignore log.xml
	@chmod +x /tmp/$(SUIT_NAME)/libvirt-test-api.py
	@cd /tmp; tar czSpf $(SUIT_NAME).tar.gz $(SUIT_NAME)
	@rm -rf /tmp/$(SUIT_NAME)
	@cp /tmp/$(SUIT_NAME).tar.gz .
	@rm -f /tmp/$(SUIT_NAME).tar.gz
	@echo " "
	@echo "the archive is $(SUIT_NAME).tar.gz"

clean:
	@find . -name "*.pyc" -exec rm -f {} \;
	@rm -rf log/ log.xml
	@rm -f $(SUIT_NAME).tar.gz
