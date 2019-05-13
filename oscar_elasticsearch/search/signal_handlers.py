# pylint: disable=unused-argument
from oscar.core.loading import get_model, get_class
from django.db.models.signals import post_delete, post_save
from wagtail.search.signal_handlers import post_delete_signal_handler

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
ProductProxy = get_model("search", "ProductProxy")
update_index = get_class("search.spooler", "update_index")


def product_post_save_signal_handler(instance, update_fields=None, **kwargs):
    update_index.spool(product_id=str(instance.pk))


def post_product_category_save_signal_handler(instance, update_fields=None, **kwargs):
    update_index.spool(product_id=str(instance.product.pk))


def product_post_delete_signal_handler(instance, **kwargs):
    return post_delete_signal_handler(ProductProxy(pk=instance.pk), **kwargs)


def category_change_handler(instance, **kwargs):
    update_index.spool(category_id=str(instance.pk))


def register_signal_handlers():
    # we must pass the save signal from the regular model through to the proxy
    # model, because the wagtail listener is attached to the proxy model, not
    # the regular model.
    post_save.connect(
        post_product_category_save_signal_handler, sender=Product.categories.through
    )
    post_save.connect(product_post_save_signal_handler, sender=Product)
    post_delete.connect(product_post_delete_signal_handler, sender=Product)
    post_save.connect(category_change_handler, sender=Category)
    post_delete.connect(category_change_handler, sender=Category)


def deregister_signal_handlers():
    # Disconnects the signal handlers for easy access in importers
    post_save.disconnect(
        post_product_category_save_signal_handler, sender=Product.categories.through
    )
    post_save.disconnect(product_post_save_signal_handler, sender=Product)
    post_delete.disconnect(product_post_delete_signal_handler, sender=Product)
    post_save.disconnect(category_change_handler, sender=Category)
    post_delete.disconnect(category_change_handler, sender=Category)
