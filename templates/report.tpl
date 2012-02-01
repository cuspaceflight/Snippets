View report online: http://snippets.cusf.co.uk/team/{{date|date:"U"}}

{% for snippet in snippets %}
{{snippet.entity.display_name|safe}}
----------------------------------------

{{snippet.content|safe}}

{% endfor %}
