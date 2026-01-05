import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app, ZONE_CONFIG

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Traffic Service" 

# Verify that it returns a list of sensors with the correct fields
def test_get_traffic_zone_structure():
    response = client.get("/traffic/zone/TEST_ZONE")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    sensor = data[0]
    assert "id" in sensor
    assert "vehicle_count" in sensor
    assert "status" in sensor
    assert sensor["zone"] == "TEST_ZONE"

# Verify that the number of sensors remains constant
def test_zone_persistence():
    zone_id = "PERSISTENCE_TEST_UNIT"
    
    resp1 = client.get(f"/traffic/zone/{zone_id}")
    count1 = len(resp1.json())
    
    resp2 = client.get(f"/traffic/zone/{zone_id}")
    count2 = len(resp2.json())
    
    assert count1 == count2