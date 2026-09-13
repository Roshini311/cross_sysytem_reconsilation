from rest_framework import serializers
from reconciliation.models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['org_id', 'name']


class DiscrepancySerializer(serializers.Serializer):
    record_id = serializers.CharField()
    location_id = serializers.CharField()
    org_id = serializers.CharField()
    reason = serializers.CharField()
    system_a_value = serializers.CharField(allow_null=True)
    system_b_value = serializers.CharField(allow_null=True)
