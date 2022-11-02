$(document).ready(function () {

    // $("#sidebar").mCustomScrollbar({
    //      theme: "minimal"
    // });

    // $('#sidebarCollapse').on('click', function () {
    //     $('#sidebar, #content').toggleClass('active');
    // });

    // $('#sidebar ul li').on('click', function () {
    //     $('#sidebar ul .active').removeClass('active');
    //     $(this).addClass('active');
    // });

    $('#search-form').on('submit', function () {
        $("#btn-submit").attr("disabled", true);
        $('#btn-submit').html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Searching...')
    });

});