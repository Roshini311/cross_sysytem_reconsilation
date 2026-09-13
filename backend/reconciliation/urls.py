from django.urls import path
from reconciliation.views import OrgListView, DiscrepancyListView

urlpatterns = [
    path('orgs/', OrgListView.as_view(), name='org-list'),
    path('discrepancies/', DiscrepancyListView.as_view(), name='discrepancy-list'),
]
