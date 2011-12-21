View report online: http://snippets.cusf.co.uk/team/{{date|date:"U"}}

{% for snippet in snippets %}{% if snippet.user %}
{{snippet.user.display_name}}
----------------------------------------

{{snippet.content}}

{% endif %}{% endfor %}
