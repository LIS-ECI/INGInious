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
function studio_create_new_contest_problem()
{
    var new_problem_id = $('#problem_id').val();
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
    alert(url);
    var problem_id = $('#problem_id').val();
    if(problem_id==""){
        alert("Select a problem first");
        return false;
    }
    window.open(url+"/course/"+course+"/"+problem_id+"/"+problem_id+".pdf",'_blank');
}