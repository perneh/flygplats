# GUI-test‑VM — bygg och starta (kort guide)

Det här skapar en **virtuell Linux‑dator** (filen `output/gui-test-vm.qcow2`) med skrivbord och golf‑appen inuti. Du behöver **inte** kunna Docker eller nätverk i detalj — följ stegen i ordning.

> **Säkerhet:** En virtuell maskin med öppet skrivbord är lämplig för **test/lab**. Dela inte maskinen på öppet internet.

---

## 0. Installera två program på din Mac (eller Linux)

1. **Packer** — [packer.io/downloads](https://developer.hashicorp.com/packer/downloads) (installera så att kommandot `packer` fungerar i Terminal).
2. **QEMU** — i Terminal: `brew install qemu` (Mac med Homebrew).

**Mac med Apple Silicon (M1/M2/M3):** du behöver också en **firmware‑fil** för virtuella ARM‑datorer. Efter `brew install qemu` finns den ofta här:

`/opt/homebrew/share/qemu/edk2-aarch64-code.fd`

(Den sökvägen ska du klistra in i steg 3 nedan.)

---

## 1. Öppna Terminal och gå till rätt mapp

Du ska stå i mappen **`flygplats/infra/gui-test-vm`** (anpassa om din klon ligger någon annanstans):

```bash
cd sökväg/till/flygplats/infra/gui-test-vm
```

---

## 2. Skapa en nyckel (används bara för att bygga VM:en)

Kör **exakt** denna rad (den skapar två filer under `http/` — de ska **inte** laddas upp till GitHub av misstag):

```bash
ssh-keygen -t ed25519 -f http/builder -N ""
```

---

## 3. Fyll i “receptfilen” för bygget

1. Kopiera mallen till en egen fil du får redigera:

   ```bash
   cp example.pkrvars.hcl min-byggfil.pkrvars.hcl
   ```

2. Öppna **`min-byggfil.pkrvars.hcl`** i en texteditor.

3. Byt ut **`REPLACE_WITH_LINE_FROM_SHA512SUMS`** mot en **riktig checksumma** för Debian‑skivan (annars stoppar `make all` med ett tydligt fel).
   - **Enklast (ingen manuell klistring):** i mappen `infra/gui-test-vm`, kör  
     `make apply-checksum VARFILE=min-byggfil.pkrvars.hcl`  
     då hämtas checksum från Debian och skrivs in i filen (första `cloud_image_checksum = ...`-raden ersätts; extra dubbletter tas bort).
   - **Alternativ:** `make checksum-print` och klistra in utskriften som raden `cloud_image_checksum = ...` (raden ska börja med `cloud_image_checksum` efter valfritt blanksteg).
   - **Alternativt i webbläsaren:** gå till  
     [https://cloud.debian.org/images/cloud/bookworm/latest/](https://cloud.debian.org/images/cloud/bookworm/latest/), öppna **`SHA512SUMS`**, hitta raden för **`debian-12-generic-arm64.qcow2`** (Apple Silicon) och sätt  
     `cloud_image_checksum = "sha512:...` med exakt samma hex som i sum‑filen (eller `sha256:...` om du använder SHA256).

4. Ändra **`frontend_git_url`** till **din** Git‑adress till flygplats‑repot (om du inte använder standardexemplet).

5. **Apple Silicon:** lägg till en rad (eller avkommentera) med firmware, t.ex.:

   ```hcl
   firmware = "/opt/homebrew/share/qemu/edk2-aarch64-code.fd"
   ```

Spara filen.

---

## 4. Förbered och bygg VM‑skivan

### Snabbväg med Make (om du har `make` installerat)

I mappen `infra/gui-test-vm` kan du först kontrollera (och på Mac med Homebrew även installera) **Packer och QEMU**:

```bash
make prep
```

Sedan kan **Make** skriva in checksum i din var‑fil (rekommenderat) eller bara visa den:

```bash
make help
make apply-checksum VARFILE=min-byggfil.pkrvars.hcl
# eller: make checksum-print   och klistra in utskriften manuellt
```

Skapa nycklar och bygg:

```bash
make keys
make all VARFILE=min-byggfil.pkrvars.hcl
```

### Manuellt (utan Make)

Kör i samma mapp (`infra/gui-test-vm`):

```bash
chmod +x scripts/00-prepare-cloud-init.sh build.sh
./scripts/00-prepare-cloud-init.sh
./build.sh -var-file=min-byggfil.pkrvars.hcl
```

Det kan ta **många minuter** första gången. När det är klart ligger resultatet här:

**`output/gui-test-vm.qcow2`**

---

## 5. Starta VM:en (enklast med UTM på Mac)

1. Installera **UTM** från [utm.app](https://mac.getutm.app/) (eller Mac App Store).
2. Öppna UTM → **File → New → Virtualize** → **Import**.
3. Välj filen **`output/gui-test-vm.qcow2`**.
4. Starta VM:en (▶︎). Du ska få **XFCE‑skrivbord** och användaren **`debian`** (inloggning sker ofta automatiskt).

**Nätverk:** om du ska styra fönster från en annan dator/container, sätt i UTM under nätverk **Bridged** (eller följ UTM:s hjälp om “Shared network”) så VM:en får ett eget IP.

---

## 6. Starta golf‑appen inne i VM:en

Öppna **Terminal** i VM:en (programmet Terminal i menyn) och kör:

```bash
/usr/local/bin/run-frontend.sh
```

Appen pratar med backend via **`API_BASE_URL`** (förinställt i `/etc/golf-gui/env`). Om backend körs på din Mac kan du behöva ändra den adressen till något som VM:en når (det kan du göra med en texteditor som **sudo** + redigera filen — be någon med Linux‑vana om du fastnar).

---

## Om något går fel

| Problem | Vad du kan prova |
|--------|-------------------|
| **Packer säger SSH timeout** | Fel checksumma i `min-byggfil.pkrvars.hcl`, eller saknad **`firmware`** på Apple Silicon. |
| **UTM startar inte disken** | Bygg om efter steg 4; kontrollera att `output/gui-test-vm.qcow2` finns och inte är 0 byte. |
| **Skrivbord syns inte** | Starta om VM:en; vänta 1–2 minuter första gången. |

---

## Mer avancerat (valfritt)

- **xdotool mot frontenden från shell** (fönsterfokus, klick, tangenter): se `XDOTOOL-LATHUND.md`.
- **Köra VM utan UTM** (kommandorad): se `scripts/run-vm-qemu-example.sh`.
- **Automatisera Packer-flödet med wrapper-skript:**
  - macOS: `scripts/packer-macos.sh all`
  - Linux: `scripts/packer-linux.sh all`
  - Vanliga delsteg: `prep`, `init`, `build`, `start-qemu`, `ssh`, `status` (kör `... help` för detaljer).
- **Proxmox-flöde (bygga + importera + template/clone):** se `README-PROXMOX.md`.
- **Ändra RAM, skärmupplösning, Git‑gren:** redigera `packer.pkr.hcl` eller lägg till `-var`‑flaggor enligt [Packer dokumentation](https://developer.hashicorp.com/packer/docs).
