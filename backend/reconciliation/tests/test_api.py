import pytest
from rest_framework.test import APIClient
from reconciliation.models import Organization, Location, SystemARecord, SystemBEntry


@pytest.mark.django_db
def test_discrepancies_requires_org_id():
    client = APIClient()
    response = client.get('/api/discrepancies/')
    assert response.status_code == 400
    assert "org_id parameter is required" in response.data["error"]


@pytest.mark.django_db
def test_tenant_api_isolation():
    client = APIClient()

    # Setup 2 Orgs with 1 Location each
    org_a = Organization.objects.create(org_id="ORG_ALPHA", name="Alpha Corp")
    org_b = Organization.objects.create(org_id="ORG_BETA", name="Beta Inc")

    loc_a = Location.objects.create(location_id="LOC_101", org=org_a)
    loc_b = Location.objects.create(location_id="LOC_201", org=org_b)

    # Org Alpha: A record exists, B missing => MISSING_IN_SYSTEM_B
    SystemARecord.objects.create(record_id="REC-A1", location_id="LOC_101", raw_value="100.00")

    # Org Beta: B entry exists, A missing => ORPHAN_IN_SYSTEM_B
    SystemBEntry.objects.create(record_ref="REC-B1", normalized_record_ref="REC-B1", location_id="LOC_201", raw_value="200.00")

    # Query Org Alpha
    res_a = client.get('/api/discrepancies/?org_id=ORG_ALPHA')
    assert res_a.status_code == 200
    data_a = res_a.data
    assert len(data_a) == 1
    assert data_a[0]["org_id"] == "ORG_ALPHA"
    assert data_a[0]["reason"] == "MISSING_IN_SYSTEM_B"

    # Query Org Beta
    res_b = client.get('/api/discrepancies/?org_id=ORG_BETA')
    assert res_b.status_code == 200
    data_b = res_b.data
    assert len(data_b) == 1
    assert data_b[0]["org_id"] == "ORG_BETA"
    assert data_b[0]["reason"] == "ORPHAN_IN_SYSTEM_B"
