# GUI test VM — bygg med Make (slipper minnas alla kommandon).
# Kör `make help` först.

.DEFAULT_GOAL := help

VARFILE ?= min-byggfil.pkrvars.hcl
DEBIAN_SUMS ?= https://cloud.debian.org/images/cloud/bookworm/latest/SHA512SUMS
DEBIAN_QCOW ?= debian-12-generic-arm64.qcow2
VM_CONSOLE_PASSWORD ?= debian

.PHONY: help prep keys keys-force prepare init build all checksum-print apply-checksum clean

help:
	@echo "Golf GUI-test-VM (Packer)"
	@echo ""
	@echo "  make prep              Kolla curl/ssh-keygen/packer/QEMU; installera via brew om det saknas (macOS/Linux med brew)"
	@echo "  make keys              Skapa builder-nyckel (hoppar över om http/builder redan finns)"
	@echo "  make keys-force        Ta bort gamla nycklar och skapa nya (kör sedan prepare/build igen)"
	@echo "  make checksum-print    Skriv färdig cloud_image_checksum-rad för $(DEBIAN_QCOW)"
	@echo "  make apply-checksum    Hämta checksum från Debian och skriv in i $(VARFILE) (slipper manuell klistring)"
	@echo "  make prepare           Generera http/user-data från mall + builder.pub"
	@echo "  make init              packer init"
	@echo "  make build             packer build -var-file=$(VARFILE)"
	@echo "  make all               prepare + init + build (samma VARFILE)"
	@echo ""
	@echo "Obs: all gör INTE keys, checksum eller apt/brew-installation. Ha VARFILE"
	@echo "     ifylld (checksum: make checksum-print) och http/builder innan all."
	@echo "Obs: build tar bort ./output innan packer build (Packer kräver tom output-katalog)."
	@echo ""
	@echo "Exempel:"
	@echo "  cp example.pkrvars.hcl min-byggfil.pkrvars.hcl"
	@echo "  make apply-checksum VARFILE=min-byggfil.pkrvars.hcl   # eller: make checksum-print och klistra in manuellt"
	@echo "  make prep && make keys && make all VARFILE=min-byggfil.pkrvars.hcl"
	@echo ""
	@echo "Variabler: VARFILE=...  DEBIAN_SUMS=...  DEBIAN_QCOW=...  VM_CONSOLE_PASSWORD=... (för amd64 byt qcow-namn)"

prep:
	@chmod +x scripts/prep-tools.sh
	@./scripts/prep-tools.sh

keys:
	@if test -f http/builder; then \
	  echo "http/builder finns redan — hoppar över ssh-keygen. Nya nycklar: make keys-force"; \
	else \
	  ssh-keygen -t ed25519 -f http/builder -N ""; \
	  echo "Skapade http/builder och http/builder.pub"; \
	fi

keys-force:
	@rm -f http/builder http/builder.pub
	@$(MAKE) keys

checksum-print:
	@echo "# Klistra in raden nedan i din .pkrvars.hcl (ersätt den gamla cloud_image_checksum-raden):"
	@curl -fsSL "$(DEBIAN_SUMS)" | grep "$(DEBIAN_QCOW)" | awk '{print "cloud_image_checksum = \"sha512:" $$1 "\""}' || { echo "Hittade ingen rad för $(DEBIAN_QCOW). Byt DEBIAN_QCOW= för t.ex. amd64."; exit 1; }

apply-checksum:
	@test -f "$(VARFILE)" || { echo "Saknar $(VARFILE). Kopiera: cp example.pkrvars.hcl $(VARFILE)"; exit 1; }
	@export PACKER_CHECKSUM_LINE=$$(curl -fsSL "$(DEBIAN_SUMS)" | grep "$(DEBIAN_QCOW)" | awk '{print "cloud_image_checksum = \"sha512:" $$1 "\""}' || { echo "Hittade ingen rad för $(DEBIAN_QCOW). Byt DEBIAN_QCOW= för t.ex. amd64."; exit 1; }); \
	tmp=$$(mktemp); \
	awk 'BEGIN{repl=ENVIRON["PACKER_CHECKSUM_LINE"]} /^[[:space:]]*cloud_image_checksum[[:space:]]*=/ { if(!done){print repl; done=1}; next} {print} END{if(!done) print repl}' "$(VARFILE)" > "$$tmp" && mv "$$tmp" "$(VARFILE)"; \
	echo "Uppdaterade cloud_image_checksum i $(VARFILE)."

prepare:
	chmod +x scripts/00-prepare-cloud-init.sh build.sh
	VM_CONSOLE_PASSWORD="$(VM_CONSOLE_PASSWORD)" ./scripts/00-prepare-cloud-init.sh

init:
	packer init .

# Only inspect real assignments (lines starting with optional space then cloud_image_checksum =).
build: prepare init
	@test -f "$(VARFILE)" || { echo "Saknar $(VARFILE). Kopiera: cp example.pkrvars.hcl $(VARFILE)"; exit 1; }
	@chk=$$(grep -E '^[[:space:]]*cloud_image_checksum[[:space:]]*=' "$(VARFILE)" 2>/dev/null || true); \
	if echo "$$chk" | grep -q 'REPLACE_WITH_LINE_FROM_SHA512SUMS'; then \
	  echo ""; \
	  echo "Fel: en rad cloud_image_checksum = ... innehåller fortfarande REPLACE_WITH_..."; \
	  echo "Visar aktiva checksum-rader:"; \
	  echo "$$chk" | sed 's/^/  /'; \
	  echo "Kör: make apply-checksum VARFILE=$(VARFILE)   (eller make checksum-print och ersätt raden manuellt)."; \
	  exit 1; \
	fi; \
	if ! echo "$$chk" | grep -qE 'sha512:[0-9a-fA-F]{128}|sha256:[0-9a-fA-F]{64}'; then \
	  echo ""; \
	  echo "Fel: ingen giltig cloud_image_checksum (sha512: 128 hex, eller sha256: 64 hex)."; \
	  echo "Kör: make apply-checksum VARFILE=$(VARFILE)   (eller make checksum-print)."; \
	  exit 1; \
	fi
	rm -rf output
	packer build -var-file="$(VARFILE)" .

all: build

clean:
	rm -rf output/ packer_cache/ .packer.d/
