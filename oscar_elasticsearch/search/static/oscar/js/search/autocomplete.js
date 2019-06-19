$.fn.autocomplete = function(url) {
    this.typeahead({
        source: function(query, process) {
            return $.get(url + '?q=' + query, function(data) {
                process(data);
            });
        },
        autoSelect: false,
        afterSelect: function(arg) {
            $('#id_q').closest("form").submit()
        }
    });
    return this;
};
