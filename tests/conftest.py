import pytest

import app as app_module


@pytest.fixture
def client():
    app_module.reset_inventory()
    app = app_module.create_app()
    app.testing = True
    return app.test_client()