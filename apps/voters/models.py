from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """Hierarchical category model for district → upazila → union → voter area"""
    name = models.CharField(max_length=255, verbose_name="Category Name")
    code = models.CharField(max_length=50, blank=True, null=True, db_index=True,
                           verbose_name="Code (first 2 digits removed)")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='children', verbose_name="Parent Category")
    full_path = models.CharField(max_length=1000, db_index=True, verbose_name="Full Path")
    has_excel = models.BooleanField(default=False, verbose_name="Has Excel Files")
    level = models.PositiveIntegerField(default=0, db_index=True, verbose_name="Hierarchy Level")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['full_path']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['parent', 'name']),
        ]

    def __str__(self):
        return self.full_path or self.name

    def get_ancestors(self):
        """Return list of ancestor categories"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors


class ExcelColumnSchema(models.Model):
    """Tracks discovered Excel column names for dynamic filtering"""
    column_name = models.CharField(max_length=255, unique=True, db_index=True)
    column_type = models.CharField(max_length=100, default='text')
    discovered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Excel Column Schema"
        verbose_name_plural = "Excel Column Schemas"
        ordering = ['column_name']

    def __str__(self):
        return self.column_name


class Voter(models.Model):
    """Voter model with normal fields for efficient search"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('unknown', 'Unknown'),
    ]
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('dead', 'Dead'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='voters',
                                 db_index=True, verbose_name="Category")
    
    # Core voter fields (indexed for fast search)
    serial = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="Serial")
    name = models.CharField(max_length=255, blank=True, null=True, db_index=True,
                           verbose_name="Name")
    voter_no = models.CharField(max_length=255, blank=True, null=True, db_index=True,
                               verbose_name="Voter No")
    father = models.CharField(max_length=255, blank=True, null=True, db_index=True,
                             verbose_name="Father Name")
    mother = models.CharField(max_length=255, blank=True, null=True, db_index=True,
                             verbose_name="Mother Name")
    profession = models.CharField(max_length=255, blank=True, null=True, db_index=True,
                                 verbose_name="Profession")
    dob = models.CharField(max_length=255, blank=True, null=True, verbose_name="Date of Birth")
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    
    gender = models.CharField(max_length=100, choices=GENDER_CHOICES, default='unknown',
                             db_index=True, verbose_name="Gender")
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='present',
                             db_index=True, verbose_name="Status")
    source_file = models.CharField(max_length=500, verbose_name="Source Excel File")
    
    # Keep JSON for any extra columns not in standard schema
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="Extra Data")
    
    # Combined search text field for fast autocomplete (denormalized for performance)
    search_text = models.TextField(blank=True, null=True, db_index=True, 
                                   verbose_name="Combined Search Text")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Voter"
        verbose_name_plural = "Voters"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'gender']),
            models.Index(fields=['voter_no']),
            models.Index(fields=['name']),
            models.Index(fields=['father']),
            models.Index(fields=['mother']),
            models.Index(fields=['gender']),
            models.Index(fields=['status']),
            models.Index(fields=['profession']),
        ]

    def __str__(self):
        return f"{self.name or 'Unknown'} - {self.voter_no or 'N/A'}"
    
    def build_search_text(self):
        """Combine all searchable fields into one text for fast searching"""
        parts = [
            self.serial or '',
            self.name or '',
            self.father or '',
            self.mother or '',
            self.address or '',
            self.voter_no or '',
            self.profession or '',
        ]
        return ' '.join(filter(None, parts)).lower()
    
    def save(self, *args, **kwargs):
        # Auto-update search_text on save
        self.search_text = self.build_search_text()
        super().save(*args, **kwargs)


class VoterStatusAudit(models.Model):
    """Audit trail for voter status changes"""
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='status_audits',
                              verbose_name="Voter")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='voter_status_changes', verbose_name="Changed By")
    old_status = models.CharField(max_length=10, choices=Voter.STATUS_CHOICES,
                                  verbose_name="Previous Status")
    new_status = models.CharField(max_length=10, choices=Voter.STATUS_CHOICES,
                                  verbose_name="New Status")
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Changed At")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP Address")

    class Meta:
        verbose_name = "Voter Status Audit"
        verbose_name_plural = "Voter Status Audits"
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['voter', 'changed_at']),
            models.Index(fields=['changed_by', 'changed_at']),
            models.Index(fields=['new_status']),
        ]

    def __str__(self):
        return f"{self.voter} - {self.old_status} → {self.new_status} by {self.changed_by}"
