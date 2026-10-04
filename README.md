# LKL turnyrinė lentelė Home Assistant

[![Atidaryti šią saugyklą Home Assistant Community Store](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=braticks&repository=lkl-standings&category=integration)

Home Assistant integracija ir Lovelace korta Lietuvos krepšinio lygos (LKL) turnyrinei lentelei.

Duomenų šaltinis – oficiali [lkl.lt](https://lkl.lt/turnyrine-lentele) turnyrinė lentelė.

## Galimybės

- sensorius `sensor.lkl_standings`;
- automatinis aktualios LKL turnyrinės lentelės nuskaitymas;
- duomenų atnaujinimas kas 30 minučių;
- komandos vieta, sužaistos rungtynės, pergalės, pralaimėjimai ir pergalių procentas;
- pelnytų ir praleistų taškų vidurkiai;
- pasirenkamas taškų skirtumo `+/−` stulpelis;
- komandų logotipai, jei juos pateikia LKL svetainė;
- integruota `custom:lkl-standings-card` Lovelace korta;
- vizualus kortos nustatymų redaktorius;
- mėgstamos komandos paryškinimas;
- 1–8 vietų atkrintamųjų zonos žymėjimas.

## Diegimas per HACS

Patogiausia naudoti viršuje esantį **Open in HACS** mygtuką.

Jei reikia pridėti rankiniu būdu:

1. Atidaryk **HACS → Integrations**.
2. Viršuje dešinėje pasirink **Custom repositories**.
3. Įrašyk `https://github.com/braticks/lkl-standings` ir pasirink tipą **Integration**.
4. Įdiek **LKL Standings**.
5. Perkrauk Home Assistant.
6. Atidaryk **Nustatymai → Įrenginiai ir paslaugos → Pridėti integraciją → LKL Standings**.

Lovelace kortos resursą integracija registruoja automatiškai, jei Home Assistant naudoja Lovelace resursų saugojimo režimą.

## Kortos naudojimas

Kortą galima pridėti per Home Assistant UI arba YAML:

```yaml
type: custom:lkl-standings-card
entity: sensor.lkl_standings
title: LKL
count: 10
favorite_team: ZAL
always_show_favorite: true
show_zones: true
team_logo_mode: icon
show_gp: true
show_pct: true
show_diff: true
compact: false
highlight_favorite: true
```

### Pagrindiniai nustatymai

- `count` – kiek komandų rodyti;
- `favorite_team` – mėgstamos komandos kodas;
- `always_show_favorite` – mėgstamą komandą rodyti net jei ji nepatenka į pasirinktą TOP;
- `team_logo_mode` – logotipo režimas: `icon`, `background` arba `none`;
- `show_gp` – rodyti sužaistų rungtynių skaičių;
- `show_pct` – rodyti pergalių procentą;
- `show_diff` – rodyti taškų skirtumą `+/−`;
- `show_zones` – pažymėti atkrintamųjų zoną;
- `compact` – kompaktiškas kortos režimas;
- `highlight_favorite` – paryškinti mėgstamą komandą.

## Kaip skaičiuojamas +/−

LKL svetainė pateikia kiekvienos komandos vidutiniškai pelnytus ir praleistus taškus. Kortos `+/−` reikšmė apskaičiuojama:

`pelnytų taškų vidurkis − praleistų taškų vidurkis`

Pavyzdžiui, jei komanda vidutiniškai pelno `97,3`, o praleidžia `76,0` taško, kortoje bus rodoma `+21,3`.

## Pastabos

Integracija nuskaito oficialią LKL turnyrinės lentelės svetainę. Jei LKL pakeistų puslapio struktūrą ar lentelės stulpelių pavadinimus, parserį gali reikėti atnaujinti.

Šis projektas nėra oficialiai susijęs su Lietuvos krepšinio lyga.