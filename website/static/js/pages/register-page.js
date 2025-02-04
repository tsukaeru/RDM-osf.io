'use strict';
var $ = require('jquery');
var $osf = require('js/osfHelpers');

var registrationUtils = require('js/registrationUtils');

var ctx = window.contextVars;
var node = ctx.node;

$(function() {
    // opt into tooltip
    $('[data-toggle="tooltip"]').tooltip();

    var viewModel;
    var selector;
    var editor = new registrationUtils.RegistrationEditor({
        schemas: '/api/v1/project/schemas/',
        create: node.urls.api + 'drafts/',
        submit: node.urls.api + 'drafts/{draft_pk}/submit/',
        update: node.urls.api + 'drafts/{draft_pk}/',
        get: node.urls.api + 'drafts/{draft_pk}/',
        draftRegistrations: node.urls.web + 'registrations/'
    }, null, true, node.registeredFrom);

    if (ctx.draft) { // if registering draft
        var draft = new registrationUtils.Draft(ctx.draft);
        viewModel = {
            draft: draft,
            editor: editor
        };
        selector = '#draftRegistrationScope';
    }
    else { // if viewing registered metadata
        var metaSchema = new registrationUtils.MetaSchema(
            ctx.node.registrationMetaSchema,
            ctx.node.registrationMetaData[ctx.node.registrationMetaSchema.id] || {}
        );
        viewModel = {
            editor: editor,
            metaSchema: metaSchema
        };
        selector = '#registrationMetaDataScope';
    }
    $osf.applyBindings(viewModel, selector);
});
