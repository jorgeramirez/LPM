/**
 * Script utilizado para actualizar relacionar un ítem con 
 * elementos de una fase anterior o siguiente.
 **/
$(function(){
    //falta probar
    var rscript = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi;
    
    $("#form_fase_anterior").submit(function(){
        var desa_pks = $("#tabla_item_fase_anterior :checkbox").filter(":checked");
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

    $("#form_fase_actual").submit(function(){
        var asig_pks = $("#tabla_item_fase_actual :checkbox").filter(":checked");
        var asig_kw = new Object();

        $(asig_pks).each(function(n){
            asig_kw[n] = $(this).attr("id");
        });
        
        $.ajax({
            type: "POST",
            dataType: "html",
            url: $(this).attr("action"),
            cache: false,
            data: asig_kw,
            complete: function(jqXHR, textStatus){
                var responseText = jqXHR.responseText;
                window.location.href = responseText;
                /*var tbl_html = jQuery("<div>")
                               .append(responseText.replace(rscript, ""))
                               .find("#tabla_item_fase_actual");
                $("#tabla_item_fase_actual").html(tbl_html);*/
            }
        });
        return false;
    });
});
