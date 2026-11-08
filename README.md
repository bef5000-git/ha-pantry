# Pantry for Home Assistant

Brings meal plans and meal-prep tasks from **Pantry** (a self-hosted meal planner that runs on a PC on your
network) into Home Assistant, so your own automations can remind you to take the chicken out of the freezer
or start the crock pot.

The integration only reads from Pantry. It never sends notifications itself: your automations decide when,
how, and to whom.

## Requirements

- Pantry **2026.11.08 or later**, running on a PC on the same network as Home Assistant.
- Home Assistant **2025.1** or later.

## Install with HACS

1. HACS → three-dot menu (top right) → **Custom repositories**.
2. Repository: `https://github.com/bef5000-git/ha-pantry`, type **Integration** → **Add**.
3. Search HACS for **Pantry** → **Download**.
4. Restart Home Assistant.
5. On the Pantry PC, run `ha-integration-token.bat` in the Pantry folder. It shows Pantry's address and a
   token.
6. Settings → Devices & services → **Add integration** → **Pantry**, and enter the address and token.

Updates show up in HACS like any other integration; restart Home Assistant after updating.

## Entities

All refresh every 5 minutes.

| Entity | State | Attributes |
| --- | --- | --- |
| `binary_sensor.pantry_online` | `on` when Home Assistant reached Pantry on its last check, `off` when it couldn't (diagnostic) | |
| `sensor.pantry_prep_today` | Number of prep tasks for today's meals | `summary` (one task per line), `tasks`, `meals` |
| `sensor.pantry_prep_tonight` | Number of tasks to do tonight for tomorrow's meals | same |
| `sensor.pantry_next_prep` | Timestamp of the next task, at Pantry's time for it | `task`, `meal`, `slot`, `meal_date`, `summary` |
| `sensor.pantry_meals_today` | Today's meals, e.g. `Oatmeal (breakfast), Chicken Tacos (dinner)` | `breakfast`, `lunch`, `dinner`, `meals` |
| `calendar.pantry_meal_prep` | Each prep task as a 15-minute event at Pantry's time | event summary = the task, description = which meal |
| `calendar.pantry_meals` | Each planned meal as an all-day event | ingredients and prep in the description |

When Pantry can't be reached, `binary_sensor.pantry_online` turns `off` and the other entities show
`unavailable`; they come back on the next successful check. The integration still sets up if the PC is off
when Home Assistant starts.

Unique ids are built from an id Pantry makes once on the PC, plus a fixed key per entity
(`<pantry id>_prep_today`, …). They stay the same if the PC's address changes or the integration is removed
and added again. To change the address, use **Reconfigure** on the integration, or add it again: the same
Pantry is recognized and updated, not duplicated.

## Repairs

Pantry and this integration each say which version of the other they need. When they don't match, a notice
appears under Settings → System → Repairs:

- **Update Pantry on your PC**: Pantry is older than this integration needs.
- **Update the Pantry integration**: Pantry needs a newer integration; update it in HACS.

The notice clears itself within 5 minutes of the update.

## Example automations

[`example-automations.yaml`](example-automations.yaml) has a morning and an evening reminder, a reminder for
each task at its own time (calendar trigger with an offset), and a block to add to an automation you already
have. A morning one:

```yaml
alias: "Pantry: morning meal prep"
triggers:
  - trigger: time
    at: "06:45:00"
conditions:
  - condition: numeric_state
    entity_id: sensor.pantry_prep_today
    above: 0
actions:
  - action: notify.mobile_app_YOUR_PHONE
    data:
      title: "Meal prep today"
      message: "{{ state_attr('sensor.pantry_prep_today', 'summary') }}"
```

A time trigger can also follow `sensor.pantry_next_prep` directly, with an offset.

## Privacy

The integration talks only to the Pantry address you enter, with the token you enter (stored in Home
Assistant's config entry). It reads planned meals, ingredients and prep tasks; it can't change anything in
Pantry.

## Development

```
pip install -r requirements_test.txt
pytest
```

The tests use a fake Pantry with made-up meals.
