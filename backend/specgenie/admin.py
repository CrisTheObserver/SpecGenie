from django.contrib import admin
from .models import Category, Prompt, GroundTruthAttribute, GroundTruthProduct, ProductAttribute, PromptRole, PromptLang

class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(PromptRole)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(PromptLang)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(Prompt)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(GroundTruthAttribute)
class GroundTruthAttributeAdmin(admin.ModelAdmin):
    pass

@admin.register(GroundTruthProduct)
class GroundTruthProductAdmin(admin.ModelAdmin):
    inlines = [ProductAttributeInline]

@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    pass