from django.contrib import admin
from .models import Medicine

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'batch_number', 'manufacturer', 'uid', 'expiry_date')
    search_fields = ('name', 'manufacturer', 'uid', 'batch_number')
    list_filter = ('manufacturer', 'expiry_date')