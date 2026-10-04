# LKL Standings for Home Assistant

Home Assistant custom integration + Lovelace card for the current Lithuanian Basketball League (LKL) standings.

Data source: the official [lkl.lt](https://lkl.lt/turnyrine-lentele) standings page.

## Features

- `sensor.lkl_standings`
- current-season standings from LKL.lt
- 30-minute refresh
- team position, games, wins, losses and win percentage
- team logos when provided by the LKL standings HTML
- bundled `custom:lkl-standings-card`
- visual card editor
- favorite-team highlight
- 1–8 playoff-zone indicator

## Installation

### HACS custom repository

Add `https://github.com/braticks/lkl-standings` as an **Integration** repository, install it, then restart Home Assistant.

After restart: **Settings → Devices & services → Add integration → LKL Standings**.

The bundled Lovelace card resource is registered automatically in storage mode.

## Card

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
compact: false
highlight_favorite: true
```

## Notes

The integration reads the official LKL standings table. If LKL.lt changes its table markup or column names, the parser may need an update.
