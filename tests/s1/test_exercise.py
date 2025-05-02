import os
import pytest
from fastapi.testclient import TestClient
from bdi_api.main import app
from bdi_api.settings import settings

client = TestClient(app)
API_PREFIX = "/api/s1"

@pytest.fixture
def setup_test_data():
    # Create test directories
    os.makedirs(settings.raw_dir, exist_ok=True)
    os.makedirs(settings.prepared_dir, exist_ok=True)
    yield
    # Cleanup after tests
    try:
        if os.path.exists(settings.raw_dir):
            for file in os.listdir(settings.raw_dir):
                file_path = os.path.join(settings.raw_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        if os.path.exists(settings.prepared_dir):
            for file in os.listdir(settings.prepared_dir):
                file_path = os.path.join(settings.prepared_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    except PermissionError:
        # If we can't clean up, just continue
        pass

def test_download_endpoint(setup_test_data):
    response = client.post(f"{API_PREFIX}/aircraft/download?file_limit=1")
    assert response.status_code == 200
    assert response.json() == "OK"
    # Verify file was downloaded
    files = os.listdir(os.path.join(settings.raw_dir))
    assert len(files) > 0
    assert any(file.endswith('.json.gz') for file in files)

def test_prepare_endpoint(setup_test_data):
    # First download some data
    client.post(f"{API_PREFIX}/aircraft/download?file_limit=1")
    # Then prepare it
    response = client.post(f"{API_PREFIX}/aircraft/prepare")
    assert response.status_code == 200
    assert response.json() == "OK"
    # Verify parquet files were created
    assert os.path.exists(os.path.join(settings.prepared_dir, "aircraft_info.parquet"))
    assert os.path.exists(os.path.join(settings.prepared_dir, "positions.parquet"))
    assert os.path.exists(os.path.join(settings.prepared_dir, "statistics.parquet"))

def test_list_aircraft(setup_test_data):
    # Prepare test data
    client.post(f"{API_PREFIX}/aircraft/download?file_limit=1")
    client.post(f"{API_PREFIX}/aircraft/prepare")
    
    response = client.get(f"{API_PREFIX}/aircraft")
    assert response.status_code == 200
    aircraft_list = response.json()
    assert isinstance(aircraft_list, list)
    if len(aircraft_list) > 0:
        assert all(isinstance(aircraft, dict) for aircraft in aircraft_list)
        assert all("icao" in aircraft for aircraft in aircraft_list)

def test_aircraft_positions(setup_test_data):
    # Prepare test data
    client.post(f"{API_PREFIX}/aircraft/download?file_limit=1")
    client.post(f"{API_PREFIX}/aircraft/prepare")
    
    # Get an aircraft ICAO from the list
    aircraft_list = client.get(f"{API_PREFIX}/aircraft").json()
    if len(aircraft_list) > 0:
        test_icao = aircraft_list[0]["icao"]
        response = client.get(f"{API_PREFIX}/aircraft/{test_icao}/positions")
        assert response.status_code == 200
        positions = response.json()
        assert isinstance(positions, list)
        if len(positions) > 0:
            assert all(isinstance(pos, dict) for pos in positions)
            assert all("lat" in pos and "lon" in pos for pos in positions)

def test_aircraft_stats(setup_test_data):
    # Prepare test data
    client.post(f"{API_PREFIX}/aircraft/download?file_limit=1")
    client.post(f"{API_PREFIX}/aircraft/prepare")
    
    # Get an aircraft ICAO from the list
    aircraft_list = client.get(f"{API_PREFIX}/aircraft").json()
    if len(aircraft_list) > 0:
        test_icao = aircraft_list[0]["icao"]
        response = client.get(f"{API_PREFIX}/aircraft/{test_icao}/stats")
        assert response.status_code == 200
        stats = response.json()
        assert isinstance(stats, dict)
        assert "alt_baro" in stats
        assert "gs" in stats
        assert "emergency" in stats

def test_invalid_icao(setup_test_data):
    response = client.get(f"{API_PREFIX}/aircraft/INVALID/positions")
    assert response.status_code == 404
    
    response = client.get(f"{API_PREFIX}/aircraft/invalid/stats")
    assert response.status_code == 404
