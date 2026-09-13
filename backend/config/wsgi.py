import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# Auto-initialize database & import CSV data on deployment startup
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)
    from reconciliation.models import SystemARecord
    if SystemARecord.objects.count() == 0:
        call_command('import_data')
except Exception as e:
    print(f"Cloud deployment DB init log: {e}")
