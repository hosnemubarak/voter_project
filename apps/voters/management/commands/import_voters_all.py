import os
import re
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from apps.voters.models import Category, Voter, ExcelColumnSchema


class Command(BaseCommand):
    help = 'Import voter data from Excel files without duplicate checks - imports all data as-is'

    def add_arguments(self, parser):
        parser.add_argument(
            '--base-path',
            type=str,
            default=os.getenv('VOTER_DATA_PATH', 'election_votar_data'),
            help='Base path to scan for voter data folders (default from VOTER_DATA_PATH env variable)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data before import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )

    def handle(self, *args, **options):
        base_path = Path(options['base_path'])
        dry_run = options['dry_run']
        
        if not base_path.exists():
            self.stderr.write(self.style.ERROR(f'Base path does not exist: {base_path}'))
            return

        if options['clear'] and not dry_run:
            self.stdout.write('Clearing existing data...')
            Voter.objects.all().delete()
            Category.objects.all().delete()
            ExcelColumnSchema.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Data cleared.'))

        self.stdout.write(f'Scanning: {base_path}')
        self.stdout.write(self.style.WARNING('NOTE: This command imports ALL data without duplicate checks'))
        
        self.categories_created = 0
        self.voters_created = 0
        self.excel_files_processed = 0
        self.dry_run = dry_run

        self._scan_directory(base_path, parent=None, level=0)

        self.stdout.write(self.style.SUCCESS(
            f'\nImport complete!\n'
            f'  Categories created: {self.categories_created}\n'
            f'  Excel files processed: {self.excel_files_processed}\n'
            f'  Voters created: {self.voters_created}'
        ))

    def _extract_code(self, folder_name):
        """Extract code by removing first 2 digits if folder name is numeric"""
        if folder_name.isdigit() and len(folder_name) > 2:
            return folder_name[2:]
        return None

    def _parse_filename(self, filename):
        """Parse Excel filename to extract metadata like gender"""
        filename_lower = filename.lower()
        
        gender = 'unknown'
        if 'female' in filename_lower:
            gender = 'female'
        elif 'male' in filename_lower:
            gender = 'male'
        
        return {'gender': gender}

    def _get_or_create_category(self, name, parent, full_path, level):
        """Get or create a category"""
        code = self._extract_code(name)
        
        if self.dry_run:
            self.stdout.write(f'  [DRY-RUN] Would create category: {full_path}')
            self.categories_created += 1
            return None
        
        category, created = Category.objects.get_or_create(
            full_path=full_path,
            defaults={
                'name': name,
                'code': code,
                'parent': parent,
                'level': level,
                'has_excel': False
            }
        )
        
        if created:
            self.categories_created += 1
            self.stdout.write(f'  Created category: {full_path}')
        
        return category

    def _scan_directory(self, path, parent, level):
        """Recursively scan directory and create categories"""
        try:
            entries = list(path.iterdir())
        except PermissionError:
            self.stderr.write(self.style.WARNING(f'Permission denied: {path}'))
            return

        subdirs = sorted([e for e in entries if e.is_dir()])
        excel_files = sorted([e for e in entries if e.is_file() and e.suffix.lower() == '.xlsx'])

        for subdir in subdirs:
            folder_name = subdir.name
            
            if parent:
                full_path = f"{parent.full_path}/{folder_name}" if parent else folder_name
            else:
                full_path = folder_name
            
            category = self._get_or_create_category(folder_name, parent, full_path, level)
            
            child_excel_files = list(subdir.glob('*.xlsx'))
            if child_excel_files and category and not self.dry_run:
                category.has_excel = True
                category.save(update_fields=['has_excel'])
            
            self._scan_directory(subdir, category, level + 1)

        if excel_files and parent:
            self._process_excel_files(excel_files, parent)

    def _process_excel_files(self, excel_files, category):
        """Process Excel files and import voter data WITHOUT duplicate checks"""
        for excel_path in excel_files:
            self.stdout.write(f'  Processing: {excel_path.name}')
            
            metadata = self._parse_filename(excel_path.name)
            
            if self.dry_run:
                self.stdout.write(f'    [DRY-RUN] Would import from: {excel_path.name}')
                self.excel_files_processed += 1
                continue

            try:
                df = pd.read_excel(excel_path)
                
                self._register_columns(df.columns.tolist())
                
                voters_to_create = []
                
                for _, row in df.iterrows():
                    # Extract standard fields
                    def get_value(col_names):
                        for col in col_names:
                            if col in row.index:
                                val = row[col]
                                if pd.isna(val):
                                    return None
                                return str(int(val)) if isinstance(val, float) and val == int(val) else str(val)
                        return None
                    
                    serial = get_value(['Serial', 'serial', 'SL', 'sl', 'S.N.', 'SN'])
                    name = get_value(['Name', 'name', 'NAME', 'নাম'])
                    voter_no = get_value(['Voter No', 'voter_no', 'VoterNo', 'VOTER NO', 'ভোটার নম্বর'])
                    father = get_value(['Father', 'father', 'FATHER', 'Father Name', 'পিতা'])
                    mother = get_value(['Mother', 'mother', 'MOTHER', 'Mother Name', 'মাতা'])
                    profession = get_value(['Profession', 'profession', 'PROFESSION', 'পেশা'])
                    dob = get_value(['DOB', 'dob', 'Date of Birth', 'DateOfBirth', 'জন্ম তারিখ'])
                    address = get_value(['Address', 'address', 'ADDRESS', 'ঠিকানা'])
                    
                    # NO DUPLICATE CHECKS - Import all data as-is
                    
                    # Collect any extra columns not in standard schema
                    standard_cols = {'Serial', 'serial', 'SL', 'sl', 'S.N.', 'SN',
                                   'Name', 'name', 'NAME', 'নাম',
                                   'Voter No', 'voter_no', 'VoterNo', 'VOTER NO', 'ভোটার নম্বর',
                                   'Father', 'father', 'FATHER', 'Father Name', 'পিতা',
                                   'Mother', 'mother', 'MOTHER', 'Mother Name', 'মাতা',
                                   'Profession', 'profession', 'PROFESSION', 'পেশা',
                                   'DOB', 'dob', 'Date of Birth', 'DateOfBirth', 'জন্ম তারিখ',
                                   'Address', 'address', 'ADDRESS', 'ঠিকানা'}
                    
                    extra_data = {}
                    for col in df.columns:
                        if col not in standard_cols:
                            val = row[col]
                            if not pd.isna(val):
                                extra_data[col] = str(val) if not isinstance(val, (int, float)) else val
                    
                    voters_to_create.append(Voter(
                        category=category,
                        gender=metadata['gender'],
                        source_file=excel_path.name,
                        serial=serial,
                        name=name,
                        voter_no=voter_no,
                        father=father,
                        mother=mother,
                        profession=profession,
                        dob=dob,
                        address=address,
                        extra_data=extra_data
                    ))
                
                with transaction.atomic():
                    Voter.objects.bulk_create(voters_to_create, batch_size=1000)
                
                self.voters_created += len(voters_to_create)
                self.excel_files_processed += 1
                
                msg = f'    Imported {len(voters_to_create)} voters from {excel_path.name} (no duplicate checks)'
                self.stdout.write(self.style.SUCCESS(msg))
                
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'    Error processing {excel_path.name}: {e}'))

    def _register_columns(self, columns):
        """Register discovered Excel columns in the schema table"""
        for col in columns:
            ExcelColumnSchema.objects.get_or_create(
                column_name=col,
                defaults={'column_type': 'text'}
            )
