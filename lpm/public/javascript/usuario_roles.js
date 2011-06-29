/**
 * Script utilizado para actualizar las tablas de roles
 * asignados y no asignados al usuario.
 **/
$(function(){

    var rscript = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi;
    
    $("#form_desasignar").submit(function(){
        var desa_pks = $("#tabla_asignados :checkbox").filter(":checked");
        var desa_kw = new Object();
        
        ctx = $("#contexto").attr('value');
        val_ctx = $("#valor_contexto").attr('value');
        desa_kw[ctx] = val_ctx;
        
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
                /*var tbl_html = jQuery("<div>")
                               .append(responseText.replace(rscript, ""))
                               .find("#tabla_asignados");
                $("#tabla_asignados").html(tbl_html);
                var tbl_html = jQuery("<div>")
                               .append(responseText.replace(rscript, ""))
                               .find("#tabla_desasignados");
                $("#tabla_desasignados").html(tbl_html);*/
            }
        });
        return false;
    });

    $("#form_asignar").submit(function(){
        var asig_pks = $("#tabla_desasignados :checkbox").filter(":checked");
        var asig_kw = new Object();

        ctx = $("#contexto").attr('value');
        val_ctx = $("#valor_contexto").attr('value');
        asig_kw[ctx] = val_ctx;

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
                window.location = responseText;
                /*var tbl_html = jQuery("<div>")
                               .append(responseText.replace(rscript, ""))
                               .find("#tabla_desasignados");
                $("#tabla_desasignados").html(tbl_html);
                var tbl_html = jQuery("<div>")
                               .append(responseText.replace(rscript, ""))
                               .find("#tabla_asignados");
                $("#tabla_asignados").html(tbl_html);*/
            }
        });
        return false;
    });
});
