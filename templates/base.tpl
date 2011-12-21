<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="utf-8">
  <title>{% block title %}CUSF Snippets{% endblock %}</title>
  <link rel="stylesheet" href="/css/default.css">
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.0/jquery.min.js"></script>
  <script src="/js/snippets.js"></script>

</head>

<body>

<div class="header">
<p class="admin"><a href="/user/{{user.user_object.user_id}}">{{user.display_name}}</a> | <a href="{{logout}}">Logout</a></p>
<h1>CUSF Snippets</h1>
</div>

<div class="wrapper">

<div class="sidebar">
{% block sidebar %}{% endblock %}
</div>

<div class="main">
{% block main %}{% endblock %}
</div>

<div class="clear"></div>

</div>

<div class="footer">
<a href="/admin/projects">Project admin</a>
</div>

</body>

</html>
