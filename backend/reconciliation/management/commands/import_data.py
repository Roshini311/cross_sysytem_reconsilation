import os
import csv
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from reconciliation.models import (
    Organization,
    Location,
    SystemARecord,
    SystemBEntry,
    ImportIssue,
)
from reconciliation.services.normalizer import normalize_record_ref, normalize_decimal


class Command(BaseCommand):
    help = "Import CSV datasets (locations, system_a, system_b) into SQLite database resiliently."

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default=None,
            help='Path to data directory containing CSV files.'
        )

    def handle(self, *args, **options):
        # Determine data directory
        data_dir_arg = options.get('data_dir')
        if data_dir_arg:
            data_dir = Path(data_dir_arg)
        else:
            # Default to <project_root>/data/
            base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            data_dir = base_dir / 'data'

        self.stdout.write(f"Using data directory: {data_dir}")

        locations_file = data_dir / "locations.csv"
        system_a_file = data_dir / "system_a.csv"
        system_b_file = data_dir / "system_b.csv"

        missing_files = []
        for name, fpath in [("locations.csv", locations_file), ("system_a.csv", system_a_file), ("system_b.csv", system_b_file)]:
            if not fpath.exists():
                missing_files.append(name)

        if missing_files:
            self.stderr.write(f"ERROR: Required CSV files missing: {', '.join(missing_files)}")
            self.stderr.write("Please place valid CSV files in the data directory.")
            return

        with transaction.atomic():
            # Clear existing data for idempotent re-runs
            ImportIssue.objects.all().delete()
            SystemBEntry.objects.all().delete()
            SystemARecord.objects.all().delete()
            Location.objects.all().delete()
            Organization.objects.all().delete()

            # 1. Import locations.csv
            loc_count = 0
            with open(locations_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row_idx, row in enumerate(reader, start=2):
                    loc_id = row.get("location_id", "").strip()
                    org_id = row.get("org_id", "").strip()
                    loc_name = row.get("location_name", "").strip()

                    if not loc_id or not org_id:
                        ImportIssue.objects.create(
                            source="locations",
                            row_number=row_idx,
                            field="location_id/org_id",
                            raw_value=json.dumps(row),
                            error_message="Missing location_id or org_id"
                        )
                        continue

                    org, _ = Organization.objects.get_or_create(
                        org_id=org_id,
                        defaults={"name": org_id}
                    )
                    Location.objects.update_or_create(
                        location_id=loc_id,
                        defaults={"org": org}
                    )
                    loc_count += 1

            # 2. Import system_a.csv
            sys_a_count = 0
            with open(system_a_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row_idx, row in enumerate(reader, start=2):
                    rec_id = row.get("record_id", "").strip()
                    loc_id = row.get("location_id", "").strip()
                    raw_val = row.get("amount", "").strip()

                    dec_val, err = normalize_decimal(raw_val)
                    if err:
                        ImportIssue.objects.create(
                            source="system_a",
                            row_number=row_idx,
                            field="amount",
                            raw_value=raw_val,
                            error_message=err
                        )

                    SystemARecord.objects.create(
                        record_id=rec_id,
                        location_id=loc_id,
                        raw_value=raw_val,
                        normalized_value=dec_val,
                        raw_json=dict(row)
                    )
                    sys_a_count += 1

            # 3. Import system_b.csv
            sys_b_count = 0
            with open(system_b_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row_idx, row in enumerate(reader, start=2):
                    rec_ref = row.get("record_ref", "").strip()
                    loc_id = row.get("location_id", "").strip()
                    raw_val = row.get("amount", "").strip()

                    norm_ref = normalize_record_ref(rec_ref)
                    dec_val, err = normalize_decimal(raw_val)
                    if err:
                        ImportIssue.objects.create(
                            source="system_b",
                            row_number=row_idx,
                            field="amount",
                            raw_value=raw_val,
                            error_message=err
                        )

                    SystemBEntry.objects.create(
                        record_ref=rec_ref,
                        normalized_record_ref=norm_ref,
                        location_id=loc_id,
                        raw_value=raw_val,
                        normalized_value=dec_val,
                        raw_json=dict(row)
                    )
                    sys_b_count += 1

            issues_count = ImportIssue.objects.count()

        self.stdout.write(self.style.SUCCESS("--- Import Completed Successfully ---"))
        self.stdout.write(f"Locations imported: {loc_count}")
        self.stdout.write(f"System A rows imported: {sys_a_count}")
        self.stdout.write(f"System B rows imported: {sys_b_count}")
        self.stdout.write(f"Import issues: {issues_count}")
