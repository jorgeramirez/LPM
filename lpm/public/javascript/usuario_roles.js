/**
 * Script utilizado para actualizar las tablas de roles
 * asignados y no asignados al usuario.
 **/
$(function(){

    $("#form_desasignar").submit(function(){
        var desa_pks = $("#tabla_asignados :checkbox").filter(":checked");
        var desa_kw = new Object();
        $(desa_pks).each(function(n){
            desa_kw[n] = $(this).attr("id");
        });

        $.ajax({
            type: "POST",
            dataType: "html",
            url: $(this).attr("action"),
            cache: true,
            data: desa_kw,
            success: function(html){
                var tbl_html = jQuery("<div>").append(html).find("#tabla_asignados");
                $("#tabla_asignados").html(tbl_html);
                var tbl_html = jQuery("<div>").append(html).find("#tabla_desasignados");
                $("#tabla_desasignados").html(tbl_html);
            }
        });
        return false;
    });

    $("#form_asignar").submit(function(){
        var asig_pks = $("#tabla_desasignados :checkbox").filter(":checked");
        var asig_kw = new Object();

        $(asig_pks).each(function(n){
            asig_kw[n] = $(this).attr("id");
        });

        $.ajax({
            type: "POST",
            dataType: "html",
            url: $(this).attr("action"),
            cache: true,
            data: asig_kw,
            success: function(html){
                var tbl_html = jQuery("<div>").append(html).find("#tabla_desasignados");
                $("#tabla_desasignados").html(tbl_html);
                var tbl_html = jQuery("<div>").append(html).find("#tabla_asignados");
                $("#tabla_asignados").html(tbl_html);
            }
        });
        return false;
    });
});
