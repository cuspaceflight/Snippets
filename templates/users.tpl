{% extends "base.tpl" %}

{% block sidebar %}
<ul class="users">
<li{% if team %} class="current"{% endif %}><a href="/team/"><img src="/images/team.jpg" border="0">Weekly overview</a></li>
<li class="spacer"></li>
{% for item in projects %}{% if not item.sidebar_hide %}
<li{% if item.key.name == project.key.name %} class="current"{% endif %}><a href="/project/{{item.key.name}}">
<img src="{{item.gravatar_url}}&s=50" border="0">
{{item.display_name}}
</a></li>
{% endif %}{% endfor %}
<li class="spacer"></li>
{% for person in users %}
<li{% if person.user_object.user_id == who.user_object.user_id %} class="current"{% endif %}><a href="/user/{{person.user_object.user_id}}">
<img src="{{person.gravatar_url}}&s=50" border="0">
{{person.display_name}}
</a></li>
{% endfor %}
</ul>
{% endblock %}
