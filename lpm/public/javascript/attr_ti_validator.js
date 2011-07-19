/**
 * Validador para los atributos del tipo de item.
 **/
$(function(){
    var validator = function(tipo){
    if(tipo == "Fecha"){
            $("input#valor_por_defecto").datepicker({dateFormat: 'yy-mm-dd'});
    }else if(tipo != 'Texto'){
            $("input#valor_por_defecto").live('keyup', function(){
                $(this).val($(this).val().replace(/[^0-9]/g, ''));
            });
        }
    }
    
    var tipo = $("select[name=tipo]").val();
    validator(tipo);

    $("select[name=tipo]").live('change', function(){
        var tipo = $(this).val();
        $("input#valor_por_defecto").die().val('').datepicker("destroy");
        validator(tipo);
    });
});
