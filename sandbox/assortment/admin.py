from django.contrib import admin

from .models import AssortmentProduct, AssortmentUser


class AssortmentProductAdmin(admin.TabularInline):
    model = AssortmentProduct
    list_display = search_fields = ["product"]


class AssortmentUserAdmin(admin.ModelAdmin):
    list_display = search_fields = ["user"]
    inlines = [
        AssortmentProductAdmin
    ]
    

admin.site.register(AssortmentUser, AssortmentUserAdmin)
