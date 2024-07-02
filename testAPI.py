import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from cookHelper import getPriceFromName as gpn,servicesMenu

@pytest.fixture
def app():
  from main import app
  yield app

@pytest.mark.parametrize("endpoint, data, expected_status, expected_result", test_data)
def test_multiple_endpoints(app: FastAPI, endpoint, data, expected_status, expected_result):
  with TestClient(app) as client:
    response = client.request(method="POST", url=endpoint, json=data)  # Adjust method if needed
    assert response.status_code == expected_status
    assert response.json() == expected_result

dic = servicesMenu.serviceMenu
test_data = []
# Define your test data in a list of tuples
for i in dic.values():
  testCase =  ("/prices", {"service_Name": i}, 200, gpn(i))
  test_data.append(testCase)
