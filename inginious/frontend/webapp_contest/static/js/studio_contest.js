//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//
"use strict";


/**
 * Redirect to the studio to create a new contest
 */
function studio_create_new_contest()
{
    var contest_id = $('#new_contest_id');
    var url = [location.protocol, '//', location.host, location.pathname].join('');
    window.location.href = url + "/../" + contest_id.val() + "/contest"
}

/**
 * Load the studio, creating blocks for existing subproblems
 */
function studio_contest_load(data)
{
    jQuery.each(data, function(pid, problem)
    {
        var template = studio_get_template_for_contest_problem(problem);
        studio_create_from_contest_template(template, pid);
        studio_init_contest_template(template, pid, problem);
    });

    // Hacky fix for codemirror in collapsable elements
    var collapsable = $('#tab_subproblems').find('.collapse');
    collapsable.on('show.bs.collapse', function()
    {
        var t = this;
        setTimeout(function()
        {
            $('.CodeMirror', t).each(function(i, el)
            {
                el.CodeMirror.refresh();
            });
        }, 10);
    });

    // Must be done *after* the event definition
    if(collapsable.length != 1)
        collapsable.collapse('hide');

    $('form#edit_contest_form').on('submit', function()
    {
        studio_contest_submit();
        return false;
    });
}



/**
 * Display a message indicating the status of a save action
 */
function studio_display_contest_submit_message(content, type, dismissible)
{
    var code = getAlertCode(content, type, dismissible);
    $('#contest_edit_submit_status').html(code);

    if(dismissible)
    {
        window.setTimeout(function()
        {
            $("#contest_edit_submit_status").children().fadeTo(1000, 0).slideUp(1000, function()
            {
                $(this).remove();
            });
        }, 3000);
    }
}

/**
 * Submit the form
 */
var studio_submitting = false;
function studio_contest_submit()
{
    if(studio_submitting)
        return;
    studio_submitting = true;

    studio_display_contest_submit_message("Saving...", "info", false);

    var error = "";
    $('.contest_edit_submit_button').attr('disabled', true);

    $.each(codeEditors, function(idx, editor) {

        // Fetch the editor id
        var path = "";
        $.each(studio_file_editor_tabs, function(tpath, id) {
            if(editor.getTextArea().id == studio_file_editor_tabs[tpath] + '_editor') {
                path = tpath;
            }
        });

        if(path) {
            jQuery.ajax({
                success: function (data) {
                    if ("error" in data)
                        error += "<li>An error occurred while saving the file " + path + "</li>";
                    else
                        editor.markClean();
                },
                url: location.pathname + "/files",
                method: "POST",
                dataType: "json",
                data: {"path": path, "action": "edit_save", "content": editor.getValue()},
                async: false
            });
        }
    });

    $('form#edit_contest_form').ajaxSubmit({
        dataType: 'json',
        success: function (data) {
            if ("status" in data && data["status"] == "ok")
                error += "";
            else if ("message" in data)
                error += "<li>" + data["message"] + "</li>";
            else
                error += "<li>An internal error occurred</li>";
        },
        error: function (result) {
            error += "<li>An internal error occurred</li>";
        },
        async: false
    });

    if(error)
        studio_display_contest_submit_message("Some error(s) occurred when saving the contest: <ul>" + error + "</ul>", "danger", true);
    else
        studio_display_contest_submit_message("contest saved.", "success", true);

    $('.contest_edit_submit_button').attr('disabled', false);
    studio_submitting = false;
}

/**
 * Get the right template for a given problem
 * @param problem
 */
function studio_get_template_for_contest_problem(problem)
{
    return "#problem_basic";
}

/**
 * Create new subproblem from the data in the form
 */
function studio_create_new_contest_problem(problem="-1")
{
    if(problem!=-1){
        var new_problem_id = problem;
    }else{
        var new_problem_id = $('#problem_id').val();
    }

    if(new_problem_id==""){
        alert("Select a problem first");
        return;
    }
    if($(studio_get_contest_problem(new_problem_id)).length != 0)
    {
        alert('This problem id is already used.');
        return;
    }
    var new_subproblem_type = "problem_basic";

    studio_create_from_contest_template('#' + new_subproblem_type, new_problem_id);
    studio_init_contest_template('#' + new_subproblem_type, new_problem_id, {id: new_problem_id});
}

/**
 * Create a new template and put it at the bottom of the problem list
 * @param template
 * @param pid
 */
function studio_create_from_contest_template(template, pid)
{
    var tpl = $(template).html().replace(/PID/g, pid);
    var tplElem = $(tpl);
    $('#accordion').append(tplElem);
}

/**
 * Get the real id of the DOM element containing the problem
 * @param pid
 */
function studio_get_contest_problem(pid)
{
    return "#subproblem_well_" + pid;
}

/**
 * Init a template with data from an existing problem
 * @param template
 * @param pid
 * @param problem
 */
function studio_init_contest_template(template, pid, problem)
{
    var well = $(studio_get_contest_problem(pid));
    studio_init_contest_template_basic(well, pid, problem);
}

/**
 * Init a code template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_contest_template_basic(well, pid, problem)
{
    if("id" in problem)
        $('#name-' + pid, well).val(problem["id"]);
    if("name" in problem)
        $('#header-' + pid, well).val(problem["name"]);
}

/**
 * Delete problem
 * @param pid
 */
function studio_contest_problem_delete(pid)
{
    var well = $(studio_get_contest_problem(pid));
    if(!confirm("Are you sure that you want to delete this problem?"))
        return;
    var codeEditors_todelete = [];
    $.each(codeEditors, function(i, editor)
    {
        if(jQuery.contains(well[0], editor.getTextArea()))
            codeEditors_todelete.push(i);
    });
    $.each(codeEditors_todelete, function(_, editor_idx)
    {
        codeEditors.splice(editor_idx, 1);
    });
    well.detach();
}

/**
 * Preview a problem
 *
 */

function studio_preview_problem(course){
    var url = [location.protocol, '//', location.host].join('');
    var problem_id = $('#problem_id').val();
    if(problem_id==""){
        alert("Select a problem first");
        return false;
    }
    window.open(url+"/course/"+course+"/"+problem_id+"/"+problem_id+".pdf",'_blank');
}

/**
 * Add a new type of problem from the data in the form
 */
function studio_add_type_problem()
{
    var quantity = $('#add-quantity').val();
    if(quantity==""){
        quantity = 1;
    }
    if(quantity<0){
        alert("Quantity must be a positive number");
        return;
    }
    var technique = $('#add-technique').val();
    if(technique==""){
        alert("Technique must be non-empty");
        return;
    }
    var structure = $('#add-structure').val();
    if(structure==""){
        alert("Structure must be non-empty");
        return;
    }
    var difficulty = $('#add-difficulty').val();
    if(difficulty==""){
        difficulty = 1;
    }

    if(difficulty<=0 || difficulty>10){
        alert("Difficulty must be between 1 and 10");
        return;
    }

    var isValid = true;
    var cont = 0;

    $("tr.type").each(function(i, tr) {
      cont++;
      var item_quantity = $("td.quantity", tr).html();
      var item_technique = $("td.technique", tr).html();
      var item_structure = $("td.structure", tr).html();
      var item_difficulty = $("td.difficulty", tr).html();

      if(isValid && difficulty==item_difficulty && (technique == item_technique)){
        alert("Already exists a type of problem with the same difficulty and the same technique.");
        isValid = false;
      }
    });

    if(!isValid){
        return;
    }

    $("#generate_contest").find('tbody')
        .append($('<tr class="type">')
            .append($('<td class="quantity">')
                    .text(quantity)
            ).append($('<td class="technique">')
                    .text(technique)
            ).append($('<td class="structure">')
                    .text(structure)
            ).append($('<td class="difficulty">')
                    .text(difficulty)
            ).append($('<td class="actions">')
                    .append($('<a>')
                        .attr('onclick', '$(this).parent().parent().remove(); $("#cloned_info").find("tr[id=info-'+cont+']").remove();')
                        .text('Remove')
                    )
            )
        );
    $("#cloned_info").append($('<tr id="info-'+cont+'">').append($('<input>')
                .attr('type', 'hidden')
                .attr('id', 'quantity-'+cont)
                .attr('name', 'type['+cont+'][quantity]')
                .attr('value', quantity)
            ).append($('<input>')
                .attr('type', 'hidden')
                .attr('id', 'technique-'+cont)
                .attr('name', 'type['+cont+'][technique]')
                .attr('value', technique)
            ).append($('<input>')
                .attr('type', 'hidden')
                .attr('id', 'structure-'+cont)
                .attr('name', 'type['+cont+'][structure]')
                .attr('value', structure)
            ).append($('<input>')
                .attr('type', 'hidden')
                .attr('id', 'difficulty-'+cont)
                .attr('name', 'type['+cont+'][difficulty]')
                .attr('value', difficulty)
            )
    );
    $('#modal_file_upload').modal('hide');
    $('#add-difficulty').val("");
    $('#add-technique').val("");
    $('#add-structure').val("");
    $('#add-quantity').val("");
    $("#add-get-problem").html("");
}

function studio_generate_new_contest(){


    var count = document.getElementById("generate_contest").getElementsByTagName("tr").length;
    if(count==1){
        alert("You must have at least one type of problem.");
        return false;
    }

    $("#generate").val("1");
    $("#get_problems").val("0");

    studio_display_contest_submit_message("Saving...", "info", false);

    var error = "";
    $('.contest_generate_submit_button').attr('disabled', true);

    $("#problems_cloned").html($("#accordion").html());

    var error = "";

    $('form#generate_contest_form').ajaxSubmit({
        dataType: 'json',
        success: function (data) {
            if ("status" in data && data["status"] == "ok"){
                error += "";
                console.log(data);
                //data = JSON.parse(data);
                var problems = data["message"];
                console.log(problems);

                $.each(problems, function( index, value ) {
                  studio_create_new_contest_problem(value);
                });



            }else if ("message" in data)
                error += "<li>" + data["message"] + "</li>";
            else
                error += "<li>An internal error occurred</li>";
        },
        error: function (result) {
            error += "<li>An internal error occurred</li>";
        },
        async: false
    });

    if(error)
        studio_display_contest_submit_message("Some error(s) occurred when generating the problems: <ul>" + error + "</ul>", "danger", true);
    else
        studio_display_contest_submit_message("Problems generated.", "success", true);

    $('.contest_generate_submit_button').attr('disabled', false);
    /*

    var types = []

    $("tr.type").each(function(i, tr) {
        var item_quantity = $("td.quantity", tr).html();
        var item_technique = $("td.technique", tr).html();
        var item_structure = $("td.structure", tr).html();
        var item_difficulty = $("td.difficulty", tr).html();
        var array = {"quantity": item_quantity, "technique": item_technique, "structure": item_structure, "difficulty": item_structure};
        types.push(array);
    });
    console.log(types);

    */

}

function studio_get_len_problems(){

    $("#generate").val("0");
    $("#get_problems").val("1");

    $("#problems_cloned").html($("#accordion").html());

    $("#add-technique_cloned").val($("#add-technique").val());

    $("#add-structure_cloned").val($("#add-structure").val());

    $("#add-difficulty_cloned").val($("#add-difficulty").val());

    var error = "";

    $("#add-get-problem").val("Loading...");

    $('form#generate_contest_form').ajaxSubmit({
        success: function (data) {
            data = JSON.parse(data);
            console.log($("#add-get-problem"));
            $("#add-get-problem").html(data["message"]);
        },
        error: function (result) {
            error += "<li>An internal error occurred</li>";
        },
        async: false
    });

    if(error)
        $("#add-get-problem").val("Some error(s) occurred when getting the problems: " + error, "danger", true);
    else
        $("#add-get-problem").val("Problems generated.", "success", true);

}