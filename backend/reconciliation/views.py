from decimal import Decimal
from django.db import OperationalError, ProgrammingError
from django.core.management import call_command
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from reconciliation.models import Organization, Location, SystemARecord, SystemBEntry
from reconciliation.serializers import OrganizationSerializer, DiscrepancySerializer
from reconciliation.services.comparator import reconcile_records
from reconciliation.services.normalizer import normalize_decimal


def ensure_database_populated():
    """
    Self-healing helper for cloud deployments (e.g. Render, Vercel).
    Automatically runs migrations and imports CSV data if database tables
    do not exist or are unpopulated.
    """
    try:
        if not Organization.objects.exists():
            call_command('migrate', interactive=False)
            call_command('import_data')
    except (OperationalError, ProgrammingError, Exception):
        try:
            call_command('migrate', interactive=False)
            call_command('import_data')
        except Exception as e:
            print(f"Database initialization warning: {e}")


class OrgListView(APIView):
    """
    GET /api/orgs/
    Returns list of available tenant organizations.
    """
    def get(self, request):
        ensure_database_populated()
        orgs = Organization.objects.all()
        serializer = OrganizationSerializer(orgs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DiscrepancyListView(APIView):
    """
    GET /api/discrepancies/?org_id=<org_id>&reason=<reason>&sort=<asc|desc>
    Strictly requires org_id for tenant isolation.
    """
    def get(self, request):
        org_id = request.query_params.get('org_id')
        if not org_id:
            return Response(
                {"error": "org_id parameter is required for tenant isolation."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ensure_database_populated()

        # Retrieve locations scoped strictly to the requested tenant org
        tenant_locations = Location.objects.filter(org_id=org_id)
        location_ids = set(tenant_locations.values_list('location_id', flat=True))

        location_org_map = {loc.location_id: loc.org_id for loc in tenant_locations}

        # Query database strictly scoped to tenant locations
        records_a = list(SystemARecord.objects.filter(location_id__in=location_ids))
        records_b = list(SystemBEntry.objects.filter(location_id__in=location_ids))

        # Reconcile using pure Python service
        discrepancies = reconcile_records(
            records_a=records_a,
            records_b=records_b,
            location_org_map=location_org_map,
            target_org_id=org_id
        )

        # Server-side reason filtering if requested
        reason_filter = request.query_params.get('reason')
        if reason_filter and reason_filter.upper() != 'ALL':
            discrepancies = [d for d in discrepancies if d['reason'] == reason_filter]

        # Sorting by value if requested
        sort_order = request.query_params.get('sort')
        if sort_order in ['asc', 'desc']:
            def sort_key(item):
                val_str = item.get('system_a_value') or item.get('system_b_value') or ""
                dec, _ = normalize_decimal(val_str)
                if dec is not None:
                    return (0, dec)
                return (1, val_str)

            discrepancies.sort(key=sort_key, reverse=(sort_order == 'desc'))

        serializer = DiscrepancySerializer(discrepancies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
