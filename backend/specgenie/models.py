from django.db import models

class Category(models.Model):
    """
    Represents a category with a name.

    **Attributes:**
    - `name` (CharField): The name of the category.

    **Methods:**
    - `__str__()`: Returns the name of the category as a string.
    """
    name = models.CharField(max_length=50)
    def __str__(self):
        return f"{self.name}"

class PromptRole(models.Model):
    """
    Represents a role for a prompt.

    **Attributes:**
    - `name` (CharField): The name of the role.

    **Methods:**
    - `__str__()`: Returns the name of the role as a string.
    """
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class PromptLang(models.Model):
    """
    Represents a language for a prompt.

    **Attributes:**
    - `name` (CharField): The name of the language.

    **Methods:**
    - `__str__()`: Returns the name of the language as a string.
    """
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Prompt(models.Model):
    """
    Represents a prompt with various attributes.

    **Attributes:**
    - `category` (ForeignKey): The category associated with the prompt.
    - `role` (ForeignKey): The role associated with the prompt.
    - `lang` (ForeignKey): The language associated with the prompt.
    - `number` (IntegerField): The number of the prompt.
    - `version` (IntegerField): The version of the prompt.
    - `content` (TextField): The content of the prompt.

    **Methods:**
    - `__str__()`: Returns a string representation of the prompt.
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    role = models.ForeignKey(PromptRole, on_delete=models.CASCADE)
    lang = models.ForeignKey(PromptLang, on_delete=models.CASCADE, default=1)
    number = models.IntegerField()
    version = models.IntegerField()
    content = models.TextField()
    def __str__(self):
        return f"{self.role} Prompt {self.number} version {self.version} - {self.category}"

class GroundTruthAttribute(models.Model):
    """
    Represents an attribute associated with a category for ground truth data.

    **Attributes:**
    - `category` (ForeignKey): The category associated with the attribute.
    - `name` (CharField): The name of the attribute.

    **Methods:**
    - `__str__()`: Returns a string representation of the attribute.
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    def __str__(self):
        return f"{self.category} - {self.name}"

class GroundTruthProduct(models.Model):
    """
    Represents a product for ground truth data.

    **Attributes:**
    - `category` (ForeignKey): The category associated with the product.
    - `name` (CharField): The name of the product.
    - `brand` (CharField): The brand of the product.
    - `part_number` (CharField): The part number of the product.
    - `description` (TextField): The description of the product.

    **Methods:**
    - `__str__()`: Returns a string representation of the product.
    - `to_json()`: Returns a JSON representation of the product and its attributes.
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    def __str__(self):
        return f"{self.category} - {self.name}"
    def to_json(self):
        attributes = ProductAttribute.objects.filter(product=self)
        data = {"name": self.name}
        for attr in attributes:
            data[attr.attribute.name] = attr.value
        data["description"] = self.description
        return data

class ProductAttribute(models.Model):
    """
    Represents an attribute of a product for ground truth data.

    **Attributes:**
    - `product` (ForeignKey): The product associated with the attribute.
    - `attribute` (ForeignKey): The attribute associated with the product.
    - `value` (CharField): The value of the attribute.

    **Methods:**
    - `__str__()`: Returns a string representation of the product attribute.
    """
    product = models.ForeignKey(GroundTruthProduct, on_delete=models.CASCADE)
    attribute = models.ForeignKey(GroundTruthAttribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.product.category} - {self.attribute.name} - {self.product.name}"