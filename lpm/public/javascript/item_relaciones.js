/**
 * Script utilizado para actualizar relacionar un ítem con 
 * elementos de una fase anterior o siguiente.
 **/
$(function(){
    //falta probar
    var rscript = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi;
    
    $("#form_fase_a_relacionar").submit(function(){
        var desa_pks = $("#tabla_items_a_relacionar :checkbox").filter(":checked");
        var desa_kw = new Object();
        $(desa_pks).each(function(n){
            desa_kw[n] = $(this).attr("id");
        });
        
        $.ajax({
            type: "POST",
            dataType: "html",
            url: $(this).attr("action"),
            cache: false,
            data: desa_kw,
            complete: function(jqXHR, textStatus){
                var responseText = jqXHR.responseText;
                window.location.href = responseText;
                /*var tbl_html = jQuery("<div>")
                               .append(responseText.replace(rscript, ""))
                               .find("#tabla_item_fase_anterior");
                $("#tabla_item_fase_anterior").html(tbl_html);*/
            }
        });
        return false;
    });

});
