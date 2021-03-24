$('#quota_recalc_all').click(function (e) {
    var showModal = function () {
        $('#quota_recalc_all_modal').modal('show');
        $('body').css('overflow', 'hidden');
        $('.modal').css('overflow', 'auto');
	};
        
    showModal();
    e.preventDefault();
    
});
