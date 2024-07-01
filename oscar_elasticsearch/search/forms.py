from collections import defaultdict

from django import forms
from django.conf import settings
from django.forms.widgets import Input
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import feature_hidden

from . import settings


class SearchInput(Input):
    """
    Defining a search type widget
    """

    input_type = "search"


class BaseSearchForm(forms.Form):
    """
    Base form used for searches
    """

    # Use a tabindex of 1 so that users can hit tab on any page and it will
    # focus on the search widget.
    q = forms.CharField(
        label=_("Search"),
        widget=SearchInput(
            attrs={
                "placeholder": _("Search"),
                "tabindex": "1",
                "class": "form-control",
                "autocomplete": "off",
            }
        ),
    )

    items_per_page = forms.TypedChoiceField(
        required=False,
        choices=[(x, x) for x in settings.ITEMS_PER_PAGE_CHOICES],
        coerce=int,
        empty_value=settings.DEFAULT_ITEMS_PER_PAGE,
        widget=forms.HiddenInput(),
    )

    SORT_BY_CHOICES = settings.SORT_BY_CHOICES_SEARCH
    SORT_BY_MAP = settings.SORT_BY_MAP_SEARCH

    sort_by = forms.ChoiceField(
        label=_("Sort by"), choices=[], widget=forms.Select(), required=False
    )

    class Media:
        js = (
            "oscar/js/search/bootstrap3-typeahead.js",
            "oscar/js/search/autocomplete.js",
        )

    def __init__(self, *args, **kwargs):
        self.selected_facets = kwargs.pop("selected_facets", [])
        super().__init__(*args, **kwargs)

        self.fields["sort_by"].choices = self.get_sort_choices()

    def has_items_per_page_choices(self):
        return len(self.get_items_per_page_choices()) > 1

    def get_items_per_page_choices(self):
        return self.fields["items_per_page"].choices

    def get_sort_params(self, clean_data):
        """
        Return the parameters passed to es for sorting.
        :param clean_data:
        :return:
        """
        return self.SORT_BY_MAP.get(clean_data.get("sort_by"), None)

    def get_sort_choices(self):
        return self.SORT_BY_CHOICES

    @property
    def selected_multi_facets(self):
        """
        Validate and return the selected facets
        """
        # Process selected facets into a dict(field->[*values]) to handle
        # multi-faceting
        selected_multi_facets = defaultdict(list)

        for facet_kv in self.selected_facets:
            if ":" not in facet_kv:
                continue

            # maxsplit on 1 to prevent error when there is another : in the value
            field_name, value = facet_kv.split(":", 1)
            selected_multi_facets[field_name].append(value)

        return selected_multi_facets


class AutoCompleteForm(forms.Form):
    q = forms.CharField(
        widget=SearchInput(
            attrs={
                "placeholder": _("Search"),
                "tabindex": "1",
                "class": "form-control",
                "autocomplete": "off",
            }
        )
    )

    class Media:
        js = (
            "oscar/js/search/bootstrap3-typeahead.js",
            "oscar/js/search/autocomplete.js",
        )


class CatalogueSearchForm(BaseSearchForm):
    SORT_BY_CHOICES = settings.SORT_BY_CHOICES_CATALOGUE
    SORT_BY_MAP = settings.SORT_BY_MAP_CATALOGUE

    category = forms.IntegerField(
        required=False, label=_("Category"), widget=forms.HiddenInput()
    )
    price_min = forms.FloatField(required=False, min_value=0)
    price_max = forms.FloatField(required=False, min_value=0)

    should_be_rendered_on_category = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["q"].required = False

    def get_sort_choices(self):
        choices = super().get_sort_choices()
        if feature_hidden("reviews"):
            return [
                (key, value) for (key, value) in choices if key != settings.TOP_RATED
            ]
        else:
            return choices

    def clean(self):
        cleaned_data = super().clean()
        # Validate price ranges
        price_min = cleaned_data.get("price_min")
        price_max = cleaned_data.get("price_max")
        if price_min and price_max and price_min > price_max:
            raise forms.ValidationError("Minimum price must exceed maximum price.")


class BrowseCategoryForm(CatalogueSearchForm):
    pass


class CategoryForm(CatalogueSearchForm):
    pass


class SearchForm(BaseSearchForm):
    category = forms.IntegerField(required=False)
