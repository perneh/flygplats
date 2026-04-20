# Lathund: xdotool mot golf‑frontenden

Målet är att styra **samma X11‑skrivbord** som appen använder (`DISPLAY :0` i VM:en). Paketet **`xdotool`** är redan installerat i VM‑bilden.

---

## 1. Förberedelser i VM:en

1. Skrivbordet ska vara igång (inloggad **`debian`** / XFCE).
2. Starta appen i en terminal i VM:en om den inte redan kör:

   ```bash
   /usr/local/bin/run-frontend.sh
   ```

3. Öppna **en ny terminal** i VM:en (samma användare **`debian`** räcker ofta för X‑auth).

---

## 2. Rekommenderat: kör xdotool **inne i VM:en** mot `:0`

Sätt display och kör verktyget lokalt (ingen nätverks‑X11 behövs):

```bash
export DISPLAY=:0
```

**Hitta huvudfönstret** (titel innehåller ofta `Golf Desktop` — samma som i GUI‑testerna):

```bash
xdotool search --sync --onlyvisible --name "Golf Desktop"
```

Första raden är fönster‑ID (hex). Spara och använd:

```bash
WID=$(xdotool search --sync --onlyvisible --name "Golf Desktop" | head -1)
xdotool windowactivate "$WID"
xdotool windowfocus "$WID"
```

**Vanliga steg:**

| Syfte | Exempel |
|--------|--------|
| Klicka | `xdotool mousemove 400 300 click 1` |
| Tangenter | `xdotool key Return` eller `xdotool key ctrl+r` |
| Text | `xdotool type --delay 50 'Min text'` |
| Lista fönster | `xdotool search --name Golf` |

Tips: `xwininfo` (paketet `x11-utils`, redan installerat) — klicka på ett fönster för att se namn och geometri.

### Exempel: Players‑menyn → **Add player**‑dialogen

I koden heter menyalternativet **`Add…`** (med ellipsis). Själva dialogrutan får titeln **`Add player`** när den öppnas (`PlayerProfileDialog` i `main_window.py`). Under **Players** ligger menyordningen:

1. **List from API…**
2. **Add…** ← öppnar “Add player”
3. **Manage…**
4. **Personal scorecard…**

**Manuellt:** klicka **Players** i menyraden i **Golf Desktop**‑fönstret → **Add…**.

**Med tangentbord + xdotool (mnemonics):** menyn **Players** har snabbtangent **Alt+P** (tecknet `&` i `&Players` i Qt). När menyn öppnas är första raden markerad (**List from API…**), så **en** pil ned väljer **Add…**.

```bash
export DISPLAY=:0
WID=$(xdotool search --sync --onlyvisible --name "Golf Desktop" | head -1)
xdotool windowactivate "$WID"
sleep 0.2
xdotool key --window "$WID" alt+p
sleep 0.3
xdotool key --window "$WID" Down Return
```

Kort paus (`sleep`) ger menyn tid att rita ut. Verifiera att dialogen finns:

```bash
xdotool search --sync --onlyvisible --name "Add player"
```

Om **Alt+P** inte öppnar **Players** (fokus, tangentbordslayout eller fönsterhanterare), använd **mus**: `xwininfo` för att läsa koordinater nära texten **Players** i menyraden, sedan `xdotool mousemove … click 1` och klick på **Add…** (kräver stabila koordinater för din upplösning).

---

## 3. Samma sak via **SSH** till VM:en

Om du kan SSH:a in som `debian`:

```bash
ssh debian@<VM-IP>
export DISPLAY=:0
xdotool search --sync --onlyvisible --name "Golf Desktop"
```

Om du får **X11‑auth**‑fel (`No protocol specified` / `Authorization required`), kör interaktivt i VM:en först:

```bash
xhost +SI:localuser:debian
```

(eller lägg regler i `/etc/golf-gui/x11-host-allow` och kör om X‑ACL enligt er labb‑rutin — se `/usr/local/bin/start-x11.sh`.)

---

## 4. Köra xdotool från **värdmaskinen** (valfritt, avancerat)

Om du startar VM med portforward för X11 (t.ex. `scripts/run-vm-qemu-example.sh`: värd `6000` → gäst `6000`), kan du prova:

```bash
export DISPLAY=127.0.0.1:0
xdotool search --sync --onlyvisible --name "Golf Desktop"
```

Då måste **xdotool** finnas på värdmaskinen också, och gästens **xhost** måste tillåta just den klienten (QEMU “user”‑nät ger ofta käll‑IP `10.0.2.2` från gästens synvinkel — en rad `inet:10.0.2.2` i `/etc/golf-gui/x11-host-allow` kan behövas i labb). I praktiken är **SSH + avsnitt 2** oftast enklast.

---

## 5. Felsökning (kort)

| Symtom | Idé |
|--------|-----|
| Inga träffar på `Golf Desktop` | Vänta tills appen startat; prova `xdotool search --name Golf` eller `xwininfo`. |
| Fel display | Kontrollera `echo $DISPLAY` — ska vara `:0` i VM. |
| `Authorization required` | `xhost` / `x11-host-allow` enligt ovan. |

---

## 6. Referens i repot

Projektets tester använder samma fönsternamn och CLI‑mönster, se `frontend/tests/support/xdotool_helpers.py` och `frontend/tests/test_02_xdotool_main_window.py`. Menytext och `setNativeMenuBar(False)` finns i `frontend/golf_desktop/ui/main_window.py` (`_build_browse_menus`, `_player_add`).
