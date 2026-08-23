import home_assistant_entities


class TestAirConditionerEntityId:
    def test_names_the_installed_climate_entity(self):
        assert (
            home_assistant_entities.AIR_CONDITIONER_ENTITY_ID
            == "climate.150633094104375_climate"
        )


class TestAllLightEntityIds:
    def test_lists_every_installed_light_in_the_order_commands_drive_them(self):
        assert home_assistant_entities.ALL_LIGHT_ENTITY_IDS == [
            "light.bedroom",
            "light.kitchen",
            "light.livingroom",
            "light.bathroom",
        ]
