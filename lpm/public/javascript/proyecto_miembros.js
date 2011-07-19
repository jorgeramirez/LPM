/**
 * Script utilizado para actualizar las tablas de 
 * miembros y no miembros de un proyecto
 **/
$(function(){

    var rscript = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi;
    
    $("#form_seleccionados").submit(function(){
        var desa_pks = $("#tabla_seleccionados :checkbox").filter(":checked");
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
                window.location = responseText;
            }
        });
        return false;
    });

});
