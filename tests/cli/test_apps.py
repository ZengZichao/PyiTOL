"""Tests for apps.py - verify all 7 Typer apps are created and registered."""

import typer

from pyitol.cli.apps import (
    config_app,
    learn_app,
    task_app,
    taxonomy_app,
    template_app,
    tree_app,
    utils_app,
)


class TestTyperAppsExist:
    """Verify all 7 Typer app instances are created and are the correct type."""

    def test_config_app_is_typer_instance(self):
        assert isinstance(config_app, typer.Typer)

    def test_template_app_is_typer_instance(self):
        assert isinstance(template_app, typer.Typer)

    def test_taxonomy_app_is_typer_instance(self):
        assert isinstance(taxonomy_app, typer.Typer)

    def test_task_app_is_typer_instance(self):
        assert isinstance(task_app, typer.Typer)

    def test_tree_app_is_typer_instance(self):
        assert isinstance(tree_app, typer.Typer)

    def test_utils_app_is_typer_instance(self):
        assert isinstance(utils_app, typer.Typer)

    def test_learn_app_is_typer_instance(self):
        assert isinstance(learn_app, typer.Typer)


class TestTyperAppsAreDistinct:
    """Verify each app is a distinct instance (not accidentally shared)."""

    def test_all_apps_are_different_objects(self):
        apps = [config_app, template_app, taxonomy_app, task_app, tree_app, utils_app, learn_app]
        for i in range(len(apps)):
            for j in range(i + 1, len(apps)):
                assert apps[i] is not apps[j], f"App at index {i} and {j} are the same object"

    def test_seven_apps_total(self):
        apps = [config_app, template_app, taxonomy_app, task_app, tree_app, utils_app, learn_app]
        assert len(apps) == 7
