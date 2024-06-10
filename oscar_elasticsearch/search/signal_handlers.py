# pylint: disable=unused-argument
from oscar.core.loading import get_model, get_class

from django.core.signals import request_finished
from django.db.models.signals import post_delete, post_save, m2m_changed

from . import settings

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
StockRecord = get_model("partner", "StockRecord")
UpdateIndex = get_class("search.update", "UpdateIndex")
ProductElasticsearchIndex = get_class("search.api.product", "ProductElasticsearchIndex")

update_index = UpdateIndex()


def push_product_update(instance):
    # if the child was changed, also update the parent
    update_index.push_product(str(instance.pk))
    if instance.is_child:
        update_index.push_product(str(instance.parent_id))


def product_post_save_signal_handler(sender, instance, **kwargs):
    if kwargs.get("raw", False):
        return

    push_product_update(instance)


def product_post_delete_signal_handler(sender, instance, **kwargs):
    if kwargs.get("raw", False):
        return

    ProductElasticsearchIndex().delete(instance.pk)


def product_category_m2m_changed_signal_handler(
    sender, instance, action, reverse, **kwargs
):
    if kwargs.get("raw", False):
        return

    if action.startswith("post"):
        if reverse:
            update_index.push_category(str(instance.pk))
        else:
            push_product_update(instance)


def category_change_handler(sender, instance, **kwargs):
    if kwargs.get("raw", False):
        return

    update_index.push_category(str(instance.pk))


def stockrecord_change_handler(sender, instance, **kwargs):
    if kwargs.get("raw", False):
        return

    push_product_update(instance.product)


def stockrecord_post_delete_handler(sender, instance, **kwargs):
    if kwargs.get("raw", False):
        return

    push_product_update(instance.product)


def register_signal_handlers():
    # we must pass the save signal from the regular model through to the proxy
    # model, because the wagtail listener is attached to the proxy model, not
    # the regular model.
    m2m_changed.connect(
        product_category_m2m_changed_signal_handler, sender=Product.categories.through
    )
    post_save.connect(product_post_save_signal_handler, sender=Product)
    post_delete.connect(product_post_delete_signal_handler, sender=Product)
    post_save.connect(category_change_handler, sender=Category)
    post_delete.connect(category_change_handler, sender=Category)
    if settings.HANDLE_STOCKRECORD_CHANGES:
        post_save.connect(stockrecord_change_handler, sender=StockRecord)
        post_delete.connect(stockrecord_post_delete_handler, sender=StockRecord)
    request_finished.connect(update_index.synchronize_searchindex)


def deregister_signal_handlers():
    # Disconnects the signal handlers for easy access in importers
    m2m_changed.disconnect(
        product_category_m2m_changed_signal_handler, sender=Product.categories.through
    )
    post_save.disconnect(product_post_save_signal_handler, sender=Product)
    post_delete.disconnect(product_post_delete_signal_handler, sender=Product)
    post_save.disconnect(category_change_handler, sender=Category)
    post_delete.disconnect(category_change_handler, sender=Category)
    if settings.HANDLE_STOCKRECORD_CHANGES:
        post_save.disconnect(stockrecord_change_handler, sender=StockRecord)
        post_delete.disconnect(stockrecord_post_delete_handler, sender=StockRecord)
    request_finished.disconnect(update_index.synchronize_searchindex)
