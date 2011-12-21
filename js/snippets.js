$(document).ready(function() {
  
  var handleSnippet = function(el) {

    var forms = $("form.snippet");
    var pres = $("pre.snippet");
    var form = $(el.target).parent().next("form.snippet");
    var textarea = form.find("textarea");   
    var pre = form.next("pre.snippet");

    var hidden = form.hasClass("hidden");

    forms.addClass("hidden");
    pres.removeClass("hidden");

    if (hidden) {
      if (pre.length > 0) {
        pre.addClass("hidden");
        textarea.val(pre.text());
      }
      form.removeClass("hidden");
      textarea.focus();
    }
    el.preventDefault();

  };

  $("a.edit").click(handleSnippet);

});

