/**
 * Script utilizado para actualizar relacionar un ítem con 
 * elementos de una fase anterior o siguiente.
 **/
$(function(){
    //falta probar
    var rscript = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi;
    
    $("#form_eliminar_relaciones").submit(function(){
        var desa_pks = $("#tabla_relaciones :checkbox").filter(":checked");
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
                var tbl_html = jQuery("<div>")
                               .append(responseText.replace(rscript, ""))
                               .find("#tabla_relaciones");
                $("#tabla_relaciones").html(tbl_html);
            }
        });
        return false;
    });

});
