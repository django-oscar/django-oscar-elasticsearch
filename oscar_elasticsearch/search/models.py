from oscar.core.loading import is_model_registered, get_model


if is_model_registered("catalogue", "Product"):

    class ProductProxy(get_model("catalogue", "Product")):
        class Meta:
            proxy = True
            app_label = "search"
