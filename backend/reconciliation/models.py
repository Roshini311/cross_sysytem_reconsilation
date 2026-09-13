from django.db import models


class Organization(models.Model):
    org_id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"Org({self.org_id})"


class Location(models.Model):
    location_id = models.CharField(max_length=100, primary_key=True)
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='locations')

    def __str__(self):
        return f"Location({self.location_id} -> {self.org_id})"


class SystemARecord(models.Model):
    record_id = models.CharField(max_length=100, db_index=True)
    location_id = models.CharField(max_length=100, db_index=True)
    raw_value = models.CharField(max_length=255, blank=True, default='')
    normalized_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    raw_json = models.JSONField(default=dict)

    def __str__(self):
        return f"SystemA({self.record_id}, val={self.raw_value})"


class SystemBEntry(models.Model):
    record_ref = models.CharField(max_length=100)
    normalized_record_ref = models.CharField(max_length=100, db_index=True)
    location_id = models.CharField(max_length=100, db_index=True)
    raw_value = models.CharField(max_length=255, blank=True, default='')
    normalized_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    raw_json = models.JSONField(default=dict)

    def __str__(self):
        return f"SystemB(ref={self.record_ref}, norm={self.normalized_record_ref})"


class ImportIssue(models.Model):
    source = models.CharField(max_length=50)
    row_number = models.IntegerField()
    field = models.CharField(max_length=50)
    raw_value = models.CharField(max_length=255, blank=True, default='')
    error_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Issue({self.source} row {self.row_number}: {self.error_message})"
