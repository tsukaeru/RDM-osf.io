'use strict';

var ko = require('knockout');
var $ = require('jquery');
var Raven = require('raven-js');
var osfHelpers = require('js/osfHelpers');
var oop = require('js/oop');
var m = require('mithril');
var bootbox = require('bootbox');
var $osf = require('js/osfHelpers');
var OauthAddonFolderPicker = require('js/oauthAddonNodeConfig')._OauthAddonNodeConfigViewModel;

var IntegromatFolderPickerViewModel = oop.extend(OauthAddonFolderPicker, {
    constructor: function(addonName, url, selector, folderPicker, opts, tbOpts) {
        var self = this;
        // TODO: [OSF-7069]
        self.super.super.constructor.call(self, addonName, url, selector, folderPicker, tbOpts);
        self.super.construct.call(self, addonName, url, selector, folderPicker, opts, tbOpts);

        // Non-OAuth fields
        self.integromatApiToken = ko.observable();
        self.userGuid = ko.observable();
        self.microsoftTeamsUserName = ko.observable();
        self.microsoftTeamsMail = ko.observable();
        self.webexMeetingsDisplayName = ko.observable();
        self.webexMeetingsMail = ko.observable();
        self.userGuidToDelete = ko.observable();
        // Treebeard config
        self.treebeardOptions = $.extend(
            {},
            OauthAddonFolderPicker.prototype.treebeardOptions,
            {   // TreeBeard Options
                columnTitles: function() {
                    return [{
                        title: 'Buckets',
                        width: '75%',
                        sort: false
                    }, {
                        title: 'Select',
                        width: '25%',
                        sort: false
                    }];
                },
                resolveToggle: function(item) {
                    return '';
                },
                resolveIcon: function(item) {
                    return m('i.fa.fa-folder-o', ' ');
                },
            },
            tbOpts
        );
    },

    connectAccount: function() {
        var self = this;
        if (!self.integromatApiToken() ){
            self.changeMessage('Please enter an API token.', 'text-danger');
            return;
        }
        $osf.block();

        return $osf.postJSON(
            self.urls().create, {
                integromat_api_token: self.integromatApiToken(),
            }
        ).done(function(response) {
            $osf.unblock();
            self.clearModal();
            $('#integromatCredentialsModal').modal('hide');
            self.changeMessage('Successfully added Integromat credentials.', 'text-success', null, true);
            self.updateFromData(response);
            self.importAuth();
        }).fail(function(xhr, status, error) {
            $osf.unblock();
            var message = '';
            var response = JSON.parse(xhr.responseText);
            if (response && response.message) {
                message = response.message;
            }
            self.changeMessage(message, 'text-danger');
            Raven.captureMessage('Could not add Integromat credentials', {
                extra: {
                    url: self.urls().importAuth,
                    textStatus: status,
                    error: error
                }
            });
        });
    },

    /** Reset all fields from Integromat credentials input modal */
    clearModal: function() {
        var self = this;
        self.message('');
        self.messageClass('text-info');
        self.integromatApiToken(null);
    },

    addWebMeetingAppsUser : function() {
        var self = this;
        if (!self.userGuid() ){
            self.changeMessage('Please enter an User Guid.', 'text-danger');
            return;
        }

        if (!self.microsoftTeamsUserName() && !self.microsoftTeamsMail() && !self.webexMeetingsDisplayName() && !self.webexMeetingsMail()){
            self.changeMessage('Please enter at least one item.', 'text-danger');
            return;
        }

        var url = self.urls().add_web_meeting_attendee;
        return osfHelpers.postJSON(
            url,
            ko.toJS({
                user_guid: self.userGuid(),
                microsoft_teams_user_name: self.microsoftTeamsUserName(),
                microsoft_teams_mail: self.microsoftTeamsMail(),
                webex_meetings_display_name: self.webexMeetingsDisplayName(),
                webex_meetings_mail: self.webexMeetingsMail()
            })
        ).done(function() {
            self.message('');
            $('#addWebMeetingAppsAttendeesModal').modal('hide');
            self.userGuid(null);
            self.microsoftTeamsUserName(null);
            self.microsoftTeamsMail(null);
            self.webexMeetingsDisplayName(null);
            self.webexMeetingsMail(null);
            self.userGuidToDelete(null);

        }).fail(function(xhr, textStatus, error) {
            var errorMessage = (xhr.status === 401) ? '401' : 'Duplicate';
            self.changeMessage(errorMessage, 'text-danger');
            Raven.captureMessage('Could not add Web Meeting Attendee', {
                url: self.url,
                textStatus: textStatus,
                error: error
            });
        });
    },

    deleteWebMeetingAppsUser : function() {
        var self = this;
        if (!self.userGuidToDelete() ){
            self.changeMessage('Please enter an User Guid.', 'text-danger');
            return;
        }
        var url = self.urls().delete_web_meeting_attendee;
        return osfHelpers.postJSON(
            url,
            ko.toJS({
                user_guid: self.userGuidToDelete(),
            })
        ).done(function() {
            self.message('');
            $('#deleteWebMeetingAppsAttendeesModal').modal('hide');
            self.userGuid(null);
            self.microsoftTeamsUserName(null);
            self.microsoftTeamsMail(null);
            self.webexMeetingsDisplayName(null);
            self.webexMeetingsMail(null);
            self.userGuidToDelete(null);

        }).fail(function(xhr, textStatus, error) {
            var errorMessage = (xhr.status === 401) ? '401' : 'Error';
            self.changeMessage(errorMessage, 'text-danger');
            Raven.captureMessage('Could not delete Web Meeting Attendee', {
                url: self.url,
                textStatus: textStatus,
                error: error
            });
        });
    }

});

// Public API
function IntegromatNodeConfig(addonName, selector, url, folderPicker, opts, tbOpts) {
    var self = this;
    self.url = url;
    self.folderPicker = folderPicker;
    opts = opts || {};
    tbOpts = tbOpts || {};
    self.viewModel = new IntegromatFolderPickerViewModel(addonName, url, selector, folderPicker, opts, tbOpts);
    self.viewModel.updateFromData();
    $osf.applyBindings(self.viewModel, selector);
}

module.exports = {
    IntegromatNodeConfig: IntegromatNodeConfig,
    _IntegromatNodeConfigViewModel: IntegromatFolderPickerViewModel
};
