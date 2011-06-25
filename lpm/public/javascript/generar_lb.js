/**
 * Script utilizado para generar una linea base
 **/
$(function(){

    var rscript = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi;
    
    $("#form_seleccionados").submit(function(){
        var gen_pks = $("#tabla_items :checkbox").filter(":checked");
        var gen_kw = new Object();
        
        $(gen_pks).each(function(n){
            gen_kw[n] = $(this).attr("id");
        });

        
        
        $.ajax({
            type: "POST",
            dataType: "html",
            url: $(this).attr("action"),
            cache: false,
            data: gen_kw,
            complete: function(jqXHR, textStatus){
                
                var responseText = jqXHR.responseText;
                window.location.href = responseText;
                /*var tbl_html = jQuery("<div>")
                               .append(responseText.replace(rscript, ""))
                               .find("#tabla_items");
                $("#tabla_items").html(tbl_html);*/
            }
        });
        return false;
    });

});
