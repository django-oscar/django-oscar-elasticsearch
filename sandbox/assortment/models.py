from django.db import models


class AssortmentUser(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="assortment_user")


class AssortmentProduct(models.Model):
    assortment_user = models.ForeignKey(AssortmentUser, on_delete=models.CASCADE, related_name="products")
    product = models.ForeignKey("catalogue.Product", on_delete=models.CASCADE)
