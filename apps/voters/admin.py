from django.contrib import admin
from .models import Category, Voter, ExcelColumnSchema, VoterStatusAudit


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'level', 'has_excel', 'full_path']
    list_filter = ['level', 'has_excel']
    search_fields = ['name', 'code', 'full_path']
    raw_id_fields = ['parent']
    ordering = ['full_path']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ['name', 'voter_no', 'gender', 'status', 'category', 'source_file', 'created_at']
    list_filter = ['gender', 'status', 'category__level']
    search_fields = ['name', 'voter_no', 'father', 'mother']
    raw_id_fields = ['category']
    readonly_fields = ['created_at']
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


@admin.register(ExcelColumnSchema)
class ExcelColumnSchemaAdmin(admin.ModelAdmin):
    list_display = ['column_name', 'column_type', 'discovered_at']
    search_fields = ['column_name']
    readonly_fields = ['discovered_at']


@admin.register(VoterStatusAudit)
class VoterStatusAuditAdmin(admin.ModelAdmin):
    list_display = ['voter', 'old_status', 'new_status', 'changed_by', 'changed_at', 'ip_address']
    list_filter = ['old_status', 'new_status', 'changed_by', 'changed_at']
    search_fields = ['voter__name', 'voter__voter_no', 'changed_by__username', 'remarks']
    raw_id_fields = ['voter', 'changed_by']
    readonly_fields = ['voter', 'changed_by', 'old_status', 'new_status', 'changed_at', 'ip_address']
    list_per_page = 50
    date_hierarchy = 'changed_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('voter', 'changed_by')
